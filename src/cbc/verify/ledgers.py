from __future__ import annotations

from cbc.models import CheckResult


def build_verification_ledger(checks: list[CheckResult]) -> list[str]:
    return [f"{check.name}: {check.status.value}" for check in checks]
