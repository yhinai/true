from __future__ import annotations

from typing import Any, Mapping

from cbc.models import MergeGateVerdict, ReviewReport


def compute_merge_gate(review: ReviewReport) -> MergeGateVerdict:
    allowed = review.verdict == "APPROVE"
    summary = "Merge allowed." if allowed else "Merge blocked pending verification concerns."
    return MergeGateVerdict(allowed=allowed, summary=summary, reasons=review.risks)


def verification_state(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    verification = run_artifact.get("verification") or run_artifact.get("verification_report") or {}
    attempts = run_artifact.get("attempts")
    if isinstance(attempts, list) and attempts:
        last_attempt = attempts[-1]
        if isinstance(last_attempt, Mapping) and isinstance(last_attempt.get("verification"), Mapping):
            verification = last_attempt["verification"]
    if not isinstance(verification, Mapping):
        verification = {}
    checks = verification.get("checks", [])
    supporting_checks = {
        str(item)
        for item in run_artifact.get("supporting_checks", [])
        if isinstance(item, str)
    }
    passed = [check["name"] for check in checks if isinstance(check, Mapping) and check.get("status") == "passed"]
    failed = [check["name"] for check in checks if isinstance(check, Mapping) and check.get("status") == "failed"]
    state = str(verification.get("status") or verification.get("verdict") or "UNPROVEN").upper()
    return {
        "state": state,
        "passing_checks": passed,
        "failing_checks": failed,
        "checks": [_summarize_check(check, supporting_checks=supporting_checks) for check in checks if isinstance(check, Mapping)],
        "unsafe_claims": int(run_artifact.get("unsafe_claims", 0) or bool(run_artifact.get("unsafe_claim"))),
    }


def merge_gate_verdict(run_artifact: Mapping[str, Any], *, risk_summary: Mapping[str, Any]) -> dict[str, Any]:
    verification = verification_state(run_artifact)
    state = verification["state"]
    unsafe_claim = bool(run_artifact.get("unsafe_claim")) or int(run_artifact.get("unsafe_claims", 0)) > 0

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


def _summarize_check(check: Mapping[str, Any], *, supporting_checks: set[str]) -> dict[str, Any]:
    details = check.get("details", {})
    artifacts = []
    if isinstance(details, Mapping):
        for key in ("counterexample_artifact", "regression_test_artifact"):
            value = details.get(key)
            if isinstance(value, str):
                artifacts.append(value)
    name = str(check.get("name", "unknown"))
    return {
        "name": name,
        "status": check.get("status"),
        "command": check.get("command"),
        "blocking": name in supporting_checks,
        "policy_reason": details.get("policy_reason") if isinstance(details, Mapping) else None,
        "artifacts": artifacts,
    }
