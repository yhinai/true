from __future__ import annotations

from typing import Any, Mapping

from cbc.models import MergeGateVerdict, ReviewReport


def compute_merge_gate(review: ReviewReport) -> MergeGateVerdict:
    allowed = review.verdict == "APPROVE"
    summary = "Merge allowed." if allowed else "Merge blocked pending verification concerns."
    return MergeGateVerdict(allowed=allowed, summary=summary, reasons=review.risks)


def verification_state(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    verification = run_artifact.get("verification") or run_artifact.get("verification_report") or {}
    if not isinstance(verification, Mapping):
        verification = {}
    checks = verification.get("checks", [])
    passed = [check["name"] for check in checks if isinstance(check, Mapping) and check.get("status") == "passed"]
    failed = [check["name"] for check in checks if isinstance(check, Mapping) and check.get("status") == "failed"]
    state = str(verification.get("status") or verification.get("verdict") or "UNPROVEN").upper()
    return {
        "state": state,
        "passing_checks": passed,
        "failing_checks": failed,
    }


def merge_gate_verdict(run_artifact: Mapping[str, Any], *, risk_summary: Mapping[str, Any]) -> dict[str, Any]:
    verification = verification_state(run_artifact)
    state = verification["state"]
    unsafe_claim = bool(run_artifact.get("unsafe_claim"))

    if unsafe_claim or risk_summary.get("risk_level") == "CRITICAL":
        verdict = "UNSAFE"
    elif state == "VERIFIED":
        verdict = "APPROVE"
    else:
        verdict = "NEEDS_CHANGES"

    return {
        "verdict": verdict,
        "reason": f"verification={state}, risk={risk_summary.get('risk_level', 'UNKNOWN')}",
    }
