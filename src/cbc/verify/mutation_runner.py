from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_mutation(workspace: Path, enabled: bool = False) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="mutation",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Mutation testing is intentionally cut by default.",
        )
    return CheckResult(name="mutation", command="disabled", status=CheckStatus.SKIPPED, stdout="Not implemented")
