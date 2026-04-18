from __future__ import annotations

from typing import Any, Mapping

from .artifacts import pick_first

VERIFIED = "VERIFIED"
FALSIFIED = "FALSIFIED"
UNPROVEN = "UNPROVEN"

APPROVE = "APPROVE"
NEEDS_CHANGES = "NEEDS_CHANGES"
UNSAFE = "UNSAFE"


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "pass", "passed", "ok"}
    if isinstance(value, (int, float)):
        return value != 0
    return False


def verification_state(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    verification_obj = pick_first(run_artifact, "verification", "verification_report")
    explicit_state = None
    checks: list[Mapping[str, Any]] = []

    if isinstance(verification_obj, Mapping):
        explicit_state = pick_first(verification_obj, "state", "status", "verdict")
        maybe_checks = pick_first(verification_obj, "checks", "results")
        if isinstance(maybe_checks, list):
            checks = [item for item in maybe_checks if isinstance(item, Mapping)]

    failed_checks: list[str] = []
    for check in checks:
        check_name = str(check.get("name") or check.get("id") or "unnamed-check")
        if "status" in check:
            status = str(check.get("status", "")).strip().lower()
            if status in {"fail", "failed", "error", "falsified"}:
                failed_checks.append(check_name)
                continue
            if status in {"pass", "passed", "ok", "verified"}:
                continue
        if "passed" in check and not _normalize_bool(check.get("passed")):
            failed_checks.append(check_name)

    normalized_state = None
    if isinstance(explicit_state, str):
        state_upper = explicit_state.strip().upper()
        if state_upper in {VERIFIED, FALSIFIED, UNPROVEN}:
            normalized_state = state_upper
        elif state_upper in {"PASS", "PASSED", "OK"}:
            normalized_state = VERIFIED
        elif state_upper in {"FAIL", "FAILED", "ERROR"}:
            normalized_state = FALSIFIED

    if normalized_state is None:
        if failed_checks:
            normalized_state = FALSIFIED
        elif checks:
            normalized_state = VERIFIED
        else:
            normalized_state = UNPROVEN

    unsafe_claim = _normalize_bool(
        pick_first(run_artifact, "unsafe_claim", "unsafe_completion")
        or (verification_obj.get("unsafe_claim") if isinstance(verification_obj, Mapping) else False)
    )

    return {
        "state": normalized_state,
        "failed_checks": failed_checks,
        "unsafe_claim": unsafe_claim,
    }


def merge_gate_verdict(
    run_artifact: Mapping[str, Any], risk_summary: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    verification = verification_state(run_artifact)
    risk_level = str((risk_summary or {}).get("risk_level", "unknown")).upper()
    state = verification["state"]
    unsafe_claim = verification["unsafe_claim"]

    if unsafe_claim:
        verdict = UNSAFE
        rationale = "Run reported completion while verification indicates unsafe claim."
    elif state == VERIFIED and risk_level not in {"HIGH", "CRITICAL"}:
        verdict = APPROVE
        rationale = "Deterministic verification artifacts are green."
    elif state == VERIFIED:
        verdict = NEEDS_CHANGES
        rationale = "Verification passed, but risk summary requires manual follow-up."
    elif state == FALSIFIED:
        verdict = NEEDS_CHANGES
        rationale = "Verification artifacts contain deterministic failures."
    else:
        verdict = NEEDS_CHANGES
        rationale = "Verification outcome is unproven."

    return {
        "verdict": verdict,
        "rationale": rationale,
        "verification": verification,
    }
