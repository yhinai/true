from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from cbc.models import CheckResult, CheckStatus


def run_hypothesis(workspace: Path, enabled: bool = False) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="hypothesis",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Hypothesis suggestions are optional in this build.",
        )
    return CheckResult(name="hypothesis", command="disabled", status=CheckStatus.SKIPPED, stdout="Not implemented")


@dataclass
class PropertyCaseResult:
    status: str
    counterexample: dict[str, Any] | None = None
    artifact_path: str | None = None


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
