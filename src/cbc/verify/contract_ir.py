from __future__ import annotations

import ast
from pathlib import Path


CONTRACT_DECORATOR_NAMES = {
    "require",
    "ensure",
    "invariant",
    "pre",
    "post",
    "contract",
    "icontract.require",
    "icontract.ensure",
    "icontract.invariant",
    "deal.pre",
    "deal.post",
    "deal.ensure",
}


def build_contract_graph(workspace: Path) -> list[str]:
    return [
        f"{entry['module']}:{entry['owner']}:{entry['decorator']}"
        for entry in extract_contract_entries(workspace)
    ]


def extract_contract_entries(workspace: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in sorted(workspace.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module = path.relative_to(workspace).with_suffix("").as_posix().replace("/", ".")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for owner, decorator in _collect_contract_nodes(tree):
            entries.append({"module": module, "owner": owner, "decorator": decorator})
    return entries


def _collect_contract_nodes(tree: ast.AST) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        owner = node.name
        for decorator in node.decorator_list:
            name = _decorator_name(decorator)
            if name in CONTRACT_DECORATOR_NAMES:
                results.append((owner, name))
    return results


def _decorator_name(decorator: ast.AST) -> str:
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        base = _decorator_name(decorator.value)
        return f"{base}.{decorator.attr}" if base else decorator.attr
    return ""
