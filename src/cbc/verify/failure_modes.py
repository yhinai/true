from __future__ import annotations

from cbc.models import CheckResult


def derive_failure_modes(checks: list[CheckResult]) -> list[str]:
    modes: list[str] = []
    for check in checks:
        if check.status.value == "failed":
            modes.append(f"{check.name}: deterministic verifier found a failing oracle or gate")
    return modes
