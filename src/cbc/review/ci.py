from __future__ import annotations

from typing import Any, Mapping


def build_ci_report(review_report: Mapping[str, Any]) -> dict[str, Any]:
    summary = review_report.get("summary", {})
    verification = summary.get("verification", {}) if isinstance(summary, Mapping) else {}
    merge_gate = summary.get("merge_gate", {}) if isinstance(summary, Mapping) else {}
    risk = summary.get("risk", {}) if isinstance(summary, Mapping) else {}
    verdict = str(merge_gate.get("verdict", "NEEDS_CHANGES"))
    return {
        "run_id": review_report.get("run_id"),
        "task_id": review_report.get("task_id"),
        "merge_gate_verdict": verdict,
        "verification_state": verification.get("state", "UNPROVEN"),
        "risk_level": risk.get("risk_level", "UNKNOWN"),
        "failing_checks": list(verification.get("failing_checks", [])),
        "supporting_checks": list(review_report.get("supporting_checks", [])),
        "exit_code": 0 if verdict == "APPROVE" else 1,
    }


def render_ci_report(report: Mapping[str, Any]) -> str:
    failing_checks = ", ".join(str(item) for item in report.get("failing_checks", [])) or "none"
    supporting_checks = ", ".join(str(item) for item in report.get("supporting_checks", [])) or "none"
    return (
        "# CI Report\n\n"
        f"- Run ID: `{report.get('run_id', 'unknown')}`\n"
        f"- Task: `{report.get('task_id', 'unknown')}`\n"
        f"- Merge Gate: `{report.get('merge_gate_verdict', 'UNKNOWN')}`\n"
        f"- Verification: `{report.get('verification_state', 'UNKNOWN')}`\n"
        f"- Risk: `{report.get('risk_level', 'UNKNOWN')}`\n"
        f"- Failing checks: `{failing_checks}`\n"
        f"- Supporting checks: `{supporting_checks}`\n"
        f"- Exit code: `{report.get('exit_code', 1)}`\n"
    )
