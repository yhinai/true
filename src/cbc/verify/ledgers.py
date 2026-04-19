from __future__ import annotations

from cbc.models import CheckResult


def build_verification_ledger(checks: list[CheckResult]) -> list[str]:
    entries: list[str] = []
    for check in checks:
        detail = f"{check.name}: {check.status.value}"
        policy_reason = check.details.get("policy_reason")
        if isinstance(policy_reason, str) and policy_reason:
            detail = f"{detail} ({policy_reason})"
        entries.append(detail)
    return entries
