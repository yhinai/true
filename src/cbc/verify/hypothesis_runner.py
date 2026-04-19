from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from cbc.models import CheckResult, CheckStatus, HypothesisCheckSpec


def run_hypothesis(
    workspace: Path,
    *,
    enabled: bool = False,
    spec: HypothesisCheckSpec | None = None,
    artifact_dir: Path | None = None,
) -> CheckResult:
    command = f"property cases via {spec.path}:{spec.function}" if spec is not None else "disabled"
    if not enabled:
        return CheckResult(
            name="hypothesis",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Hypothesis suggestions are optional in this build.",
        )
    if spec is None:
        return CheckResult(
            name="hypothesis",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="No configured property cases for this task.",
        )

    if artifact_dir is None:
        artifact_dir = workspace / ".cbc-artifacts"
    cases = expand_property_cases(spec)

    try:
        checker = load_checker(workspace, spec)
        result = run_property_cases(
            checker,
            cases,
            checker_name=spec.function,
            artifact_dir=artifact_dir / "counterexamples",
            artifact_name=spec.artifact_name,
        )
    except Exception as exc:
        return CheckResult(
            name="hypothesis",
            command=command,
            status=CheckStatus.FAILED,
            exit_code=1,
            stderr=str(exc),
            details={"configuration_error": True},
        )
    if result.status == "failed":
        regression_test_path = render_regression_test(
            artifact_dir=artifact_dir / "generated_tests",
            spec=spec,
            counterexample=result.counterexample or {},
        )
        return CheckResult(
            name="hypothesis",
            command=command,
            status=CheckStatus.FAILED,
            stdout="Property cases found a counterexample.",
            details={
                "counterexample": result.counterexample,
                "counterexample_artifact": result.artifact_path,
                "regression_test_artifact": regression_test_path,
            },
        )

    return CheckResult(
        name="hypothesis",
        command=command,
        status=CheckStatus.PASSED,
        stdout=f"Property cases passed for {len(cases)} configured examples.",
        details={"cases_checked": len(cases)},
    )


@dataclass
class PropertyCaseResult:
    status: str
    counterexample: dict[str, Any] | None = None
    artifact_path: str | None = None


def expand_property_cases(spec: HypothesisCheckSpec) -> list[Any]:
    generated = generate_cases(spec.generated_case_strategy, spec.generated_case_limit)
    ordered: list[Any] = []
    seen: set[str] = set()
    for case in [*spec.cases, *generated]:
        marker = json.dumps(case, sort_keys=True, ensure_ascii=True)
        if marker in seen:
            continue
        seen.add(marker)
        ordered.append(case)
    return ordered


def load_checker(workspace: Path, spec: HypothesisCheckSpec) -> Callable[[Any], None]:
    module_path = workspace / spec.path
    module_spec = importlib.util.spec_from_file_location(f"cbc_hypothesis_{module_path.stem}", module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Unable to load property checker module from {module_path}.")
    module = importlib.util.module_from_spec(module_spec)
    workspace_entry = str(workspace)
    inserted = False
    if workspace_entry not in sys.path:
        sys.path.insert(0, workspace_entry)
        inserted = True
    _clear_workspace_modules(workspace)
    try:
        module_spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(workspace_entry)
    checker = getattr(module, spec.function, None)
    if not callable(checker):
        raise RuntimeError(f"Property checker {spec.function!r} was not found in {module_path}.")
    return checker


def run_property_cases(
    checker: Callable[[Any], None],
    cases: list[Any],
    *,
    checker_name: str,
    artifact_dir: Path,
    artifact_name: str,
) -> PropertyCaseResult:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        try:
            checker(case)
        except Exception as exc:  # pragma: no cover - exercised via unit test
            payload = {
                "checker": checker_name,
                "input": case,
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            artifact_path = artifact_dir / artifact_name
            artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return PropertyCaseResult(
                status="failed",
                counterexample={"input": case, "message": str(exc)},
                artifact_path=str(artifact_path),
            )
    return PropertyCaseResult(status="passed")


def render_regression_test(
    *,
    artifact_dir: Path,
    spec: HypothesisCheckSpec,
    counterexample: dict[str, Any],
) -> str:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / (spec.regression_test_path or f"test_{spec.function}_regression.py")
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized_input = json.dumps(counterexample.get("input"))
    module_name = Path(spec.path).with_suffix("").as_posix().replace("/", ".")
    content = (
        f"from {module_name} import {spec.function}\n\n"
        f"def test_{spec.function}_counterexample() -> None:\n"
        f"    {spec.function}({serialized_input})\n"
    )
    target.write_text(content, encoding="utf-8")
    return str(target)


def generate_cases(strategy: str | None, limit: int) -> list[Any]:
    if strategy is None:
        return []
    if strategy == "string_edge_cases":
        corpus: list[Any] = [
            "",
            " ",
            "  ",
            "Hello",
            "Hello  World",
            "Already-Slugged",
            "MiXeD   Case Value",
            "tabs\tinside",
            " punctuation! value ",
            "123",
        ]
    elif strategy == "small_integers":
        corpus = [-2, -1, 0, 1, 2, 7, 42]
    else:
        return []
    if limit <= 0:
        return corpus
    return corpus[:limit]


def _clear_workspace_modules(workspace: Path) -> None:
    workspace = workspace.resolve()
    module_names = {
        path.stem
        for path in workspace.rglob("*.py")
        if path.name != "__init__.py"
    }
    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if isinstance(module_file, str):
            try:
                if Path(module_file).resolve().is_relative_to(workspace):
                    sys.modules.pop(name, None)
                    continue
            except (OSError, ValueError):
                pass
        if name in module_names:
            sys.modules.pop(name, None)
