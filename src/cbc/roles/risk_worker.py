from __future__ import annotations

from typing import Any

from cbc.models import VerificationReport
from cbc.review.risk import summarize_risk


def build_risk_artifact(
    *,
    diff_summary: dict[str, Any],
    verification: VerificationReport,
    unsafe_claims: int,
) -> dict[str, Any]:
    verification_summary = {
        "state": verification.verdict.value,
        "failing_checks": [
            check.name
            for check in verification.checks
            if check.status.value == "failed"
        ],
        "unsafe_claims": unsafe_claims,
    }
    summary = summarize_risk(diff_summary, verification_summary)
    return {
        "risk_level": summary["risk_level"],
        "reasons": summary["reasons"],
        "verification_state": verification.verdict.value,
        "unsafe_claims": unsafe_claims,
        "failure_modes": verification.failure_mode_ledger,
    }
