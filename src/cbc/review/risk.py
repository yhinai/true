from __future__ import annotations

from typing import Any, Mapping


def summarize_risk(
    diff_summary: Mapping[str, Any], verification_summary: Mapping[str, Any]
) -> dict[str, Any]:
    file_count = int(diff_summary.get("file_count", 0) or 0)
    high_risk_files = diff_summary.get("high_risk_files", [])
    failed_checks = verification_summary.get("failed_checks", [])
    unsafe_claim = bool(verification_summary.get("unsafe_claim", False))

    reasons: list[str] = []
    risk_level = "LOW"

    if file_count > 25:
        risk_level = "HIGH"
        reasons.append(f"Large patch touches {file_count} files.")
    elif file_count > 10:
        risk_level = "MEDIUM"
        reasons.append(f"Medium-size patch touches {file_count} files.")

    if high_risk_files:
        if risk_level in {"LOW", "MEDIUM"}:
            risk_level = "HIGH"
        reasons.append(f"Touches trust-sensitive paths: {', '.join(sorted(set(high_risk_files)))}.")

    if failed_checks:
        risk_level = "HIGH"
        reasons.append(f"Deterministic checks failed: {', '.join(failed_checks)}.")

    if unsafe_claim:
        risk_level = "CRITICAL"
        reasons.append("Unsafe completion claim recorded in verification artifacts.")

    if not reasons:
        reasons.append("No elevated risk signals in diff or verification artifacts.")

    return {"risk_level": risk_level, "reasons": reasons}
