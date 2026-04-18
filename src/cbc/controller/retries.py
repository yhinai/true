from __future__ import annotations

from cbc.models import VerificationReport


def should_retry(attempt: int, max_attempts: int, report: VerificationReport) -> bool:
    return attempt < max_attempts and report.verdict.value != "VERIFIED"
