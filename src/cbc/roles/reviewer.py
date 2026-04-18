from __future__ import annotations

from cbc.models import ReviewReport, RunLedger, VerificationVerdict


def build_review_report(ledger: RunLedger) -> ReviewReport:
    if ledger.verdict == VerificationVerdict.VERIFIED:
        verdict = "APPROVE"
    elif ledger.unsafe_claims:
        verdict = "UNSAFE"
    else:
        verdict = "NEEDS_CHANGES"
    risks = [attempt.verification.summary for attempt in ledger.attempts if attempt.verification.verdict != VerificationVerdict.VERIFIED]
    return ReviewReport(
        verdict=verdict,
        summary=ledger.final_summary,
        risks=risks,
        supporting_checks=ledger.plan.required_checks,
    )
