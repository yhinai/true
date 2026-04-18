from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from cbc.graph.callgraph import build_callgraph
from cbc.graph.dependency_dag import build_dependency_dag
from cbc.graph.slicer import slice_changed_files
from cbc.models import CheckResult, CheckStatus


@dataclass(frozen=True)
class FunctionSignature:
    module_name: str
    function_name: str
    min_positional: int
    max_positional: int | None


@dataclass(frozen=True)
class ModuleSymbols:
    module_name: str
    relative_path: str
    source_path: Path
    functions: dict[str, FunctionSignature]
    imported_modules: dict[str, str]
    imported_symbols: dict[str, tuple[str, str]]


def run_structural(workspace: Path, *, changed_files: list[str]) -> CheckResult:
    python_changed = sorted(path for path in changed_files if path.endswith(".py"))
    if not python_changed:
        return CheckResult(
            name="structural",
            command="bounded structural analysis",
            status=CheckStatus.SKIPPED,
            stdout="No Python files changed, so structural analysis was skipped.",
        )

    dependency_dag = build_dependency_dag(workspace)
    callgraph = build_callgraph(workspace)
    slice_summary = slice_changed_files(python_changed, dependency_dag=dependency_dag)
    module_index = _build_module_index(workspace)
    mismatches = _collect_mismatches(module_index, impacted_files=slice_summary["impacted_files"])

    status = CheckStatus.FAILED if mismatches else CheckStatus.PASSED
    stdout = (
        f"Found {len(mismatches)} structural mismatches in the bounded slice."
        if mismatches
        else "No structural mismatches found in the bounded slice."
    )
    return CheckResult(
        name="structural",
        command="bounded structural analysis",
        status=status,
        stdout=stdout,
        details={
            "slice": slice_summary,
            "callgraph": {path: callgraph.get(path, []) for path in slice_summary["impacted_files"] if path in callgraph},
            "dependency_dag": {
                path: dependency_dag.get(path, [])
                for path in slice_summary["impacted_files"]
                if path in dependency_dag
            },
            "mismatches": mismatches,
        },
    )


def _build_module_index(workspace: Path) -> dict[str, ModuleSymbols]:
    index: dict[str, ModuleSymbols] = {}
    path_by_module = {
        _module_name_for_path(path.relative_to(workspace).as_posix()): path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*.py")
    }

    for path in workspace.rglob("*.py"):
        relative_path = path.relative_to(workspace).as_posix()
        module_name = _module_name_for_path(relative_path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        functions: dict[str, FunctionSignature] = {}
        imported_modules: dict[str, str] = {}
        imported_symbols: dict[str, tuple[str, str]] = {}

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                positional = len(node.args.posonlyargs) + len(node.args.args)
                defaults = len(node.args.defaults)
                min_positional = positional - defaults
                max_positional = None if node.args.vararg is not None else positional
                functions[node.name] = FunctionSignature(
                    module_name=module_name,
                    function_name=node.name,
                    min_positional=min_positional,
                    max_positional=max_positional,
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    alias_name = alias.asname or alias.name.split(".")[-1]
                    if alias.name in path_by_module:
                        imported_modules[alias_name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                target_module = _resolve_from_module(module_name, node.module, node.level)
                if target_module not in path_by_module:
                    continue
                for alias in node.names:
                    alias_name = alias.asname or alias.name
                    imported_symbols[alias_name] = (target_module, alias.name)

        index[relative_path] = ModuleSymbols(
            module_name=module_name,
            relative_path=relative_path,
            source_path=path,
            functions=functions,
            imported_modules=imported_modules,
            imported_symbols=imported_symbols,
        )

    return index


def _collect_mismatches(
    module_index: dict[str, ModuleSymbols],
    *,
    impacted_files: list[str],
) -> list[dict[str, object]]:
    functions_by_module = {
        module.module_name: module.functions
        for module in module_index.values()
    }
    mismatches: list[dict[str, object]] = []
    for relative_path in impacted_files:
        module = module_index.get(relative_path)
        if module is None:
            continue
        tree = ast.parse(module.source_path.read_text(encoding="utf-8"), filename=module.relative_path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            resolved = _resolve_call(node, module)
            if resolved is None:
                continue
            target_module, target_function = resolved
            signature = functions_by_module.get(target_module, {}).get(target_function)
            if signature is None:
                continue
            observed_args = len(node.args)
            if signature.max_positional is not None and observed_args > signature.max_positional:
                mismatches.append(
                    _mismatch_payload(
                        module.relative_path,
                        target_module,
                        target_function,
                        "too_many_positional",
                        observed_args,
                        signature,
                    )
                )
            elif observed_args < signature.min_positional:
                mismatches.append(
                    _mismatch_payload(
                        module.relative_path,
                        target_module,
                        target_function,
                        "missing_required_positional",
                        observed_args,
                        signature,
                    )
                )
    return mismatches


def _resolve_call(node: ast.Call, module: ModuleSymbols) -> tuple[str, str] | None:
    if isinstance(node.func, ast.Name):
        if node.func.id in module.functions:
            return module.module_name, node.func.id
        return module.imported_symbols.get(node.func.id)

    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        imported_module = module.imported_modules.get(node.func.value.id)
        if imported_module:
            return imported_module, node.func.attr

    return None


def _mismatch_payload(
    caller_path: str,
    callee_module: str,
    callee_function: str,
    kind: str,
    observed_args: int,
    signature: FunctionSignature,
) -> dict[str, object]:
    return {
        "caller_path": caller_path,
        "callee_module": callee_module,
        "callee_function": callee_function,
        "kind": kind,
        "observed_args": observed_args,
        "expected_min_positional": signature.min_positional,
        "expected_max_positional": signature.max_positional,
    }


def _module_name_for_path(relative_path: str) -> str:
    path = Path(relative_path)
    if path.name == "__init__.py":
        return ".".join(path.parts[:-1])
    return ".".join(path.with_suffix("").parts)


def _resolve_from_module(current_module: str, target_module: str | None, level: int) -> str:
    if level == 0:
        return target_module or ""
    current_parts = current_module.split(".")
    package_parts = current_parts[:-1]
    anchor = package_parts[: len(package_parts) - (level - 1)]
    if target_module:
        return ".".join([*anchor, target_module])
    return ".".join(anchor)
