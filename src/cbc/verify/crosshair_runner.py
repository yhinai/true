from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_crosshair(workspace: Path, enabled: bool = False) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="crosshair",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="CrossHair is optional and non-blocking in this build.",
        )
    return CheckResult(name="crosshair", command="disabled", status=CheckStatus.SKIPPED, stdout="Not implemented")
