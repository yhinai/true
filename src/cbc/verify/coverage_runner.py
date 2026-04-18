from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_coverage(workspace: Path, enabled: bool = False) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="coverage",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Coverage is opt-in for this minimal build.",
        )
    return CheckResult(name="coverage", command="disabled", status=CheckStatus.SKIPPED, stdout="Not implemented")
