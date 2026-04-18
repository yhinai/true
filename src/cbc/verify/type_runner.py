from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_typecheck(workspace: Path, enabled: bool = False) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="typecheck",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Type checking is opt-in for this minimal build.",
        )
    return CheckResult(name="typecheck", command="disabled", status=CheckStatus.SKIPPED, stdout="Not implemented")
