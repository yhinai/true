from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def inspect_contracts(workspace: Path) -> CheckResult:
    return CheckResult(
        name="contracts",
        command="static inspection",
        status=CheckStatus.SKIPPED,
        stdout="Contracts are supported as an optional deeper verification layer.",
    )
