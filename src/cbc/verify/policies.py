from __future__ import annotations

from cbc.models import CheckResult, CheckStatus, VerificationVerdict


def verdict_from_checks(checks: list[CheckResult]) -> VerificationVerdict:
    if any(check.status == CheckStatus.FAILED for check in checks):
        return VerificationVerdict.FALSIFIED
    if any(check.status == CheckStatus.PASSED for check in checks):
        return VerificationVerdict.VERIFIED
    return VerificationVerdict.UNPROVEN
