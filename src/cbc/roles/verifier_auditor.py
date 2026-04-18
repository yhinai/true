from __future__ import annotations

from cbc.models import VerificationReport


def audit_verification(report: VerificationReport) -> str:
    if report.verdict.value == "VERIFIED":
        return "Deterministic verifier agrees with the completion claim."
    if report.unsafe_claim_detected:
        return "Unsafe claim detected: completion was claimed before the oracle passed."
    return "Verifier could not confirm the change."
