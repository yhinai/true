from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, CheckStatus
from cbc.verify.contract_ir import extract_contract_entries


def inspect_contracts(workspace: Path) -> CheckResult:
    try:
        entries = extract_contract_entries(workspace)
    except SyntaxError as exc:
        return CheckResult(
            name="contracts",
            command="static inspection",
            status=CheckStatus.FAILED,
            stderr=str(exc),
        )

    if not entries:
        return CheckResult(
            name="contracts",
            command="static inspection",
            status=CheckStatus.SKIPPED,
            stdout="No recognized contract decorators found in the workspace.",
        )

    modules = sorted({entry["module"] for entry in entries})
    owners = sorted({entry["owner"] for entry in entries})
    decorators = sorted({entry["decorator"] for entry in entries})
    return CheckResult(
        name="contracts",
        command="static inspection",
        status=CheckStatus.PASSED,
        stdout=f"Detected {len(entries)} contract annotations across {len(modules)} module(s).",
        details={
            "contract_entries": entries,
            "modules": modules,
            "owners": owners,
            "decorators": decorators,
        },
    )
