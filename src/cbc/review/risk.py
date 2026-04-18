from __future__ import annotations

from typing import Any, Mapping

from cbc.models import ReviewReport, RunLedger


def build_risk_summary(ledger: RunLedger) -> list[str]:
    risks = []
    if ledger.unsafe_claims:
        risks.append("unsafe claim detected before deterministic verification passed")
    if ledger.verdict.value != "VERIFIED":
        risks.append("deterministic verification did not end in VERIFIED")
    return risks


def summarize_risk(diff_summary: Mapping[str, Any], verification_summary: Mapping[str, Any]) -> dict[str, Any]:
    state = str(verification_summary.get("state", "UNPROVEN")).upper()
    failed = verification_summary.get("failing_checks", [])
    total_files = int(diff_summary.get("total_files", 0))
    unsafe_claims = int(verification_summary.get("unsafe_claims", 0))
    if unsafe_claims:
        level = "CRITICAL"
    elif state == "FALSIFIED":
        level = "CRITICAL" if failed else "HIGH"
    elif state == "UNPROVEN":
        level = "MEDIUM"
    elif total_files > 5:
        level = "MEDIUM"
    else:
        level = "LOW"

    reasons: list[str] = []
    if failed:
        reasons.append(f"{len(failed)} failing deterministic checks")
    if total_files:
        reasons.append(f"{total_files} changed files")
    if unsafe_claims:
        reasons.append("unsafe claim detected")

    return {
        "risk_level": level,
        "reasons": reasons,
    }
