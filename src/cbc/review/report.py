from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from cbc.headless_contract import REVIEW_REPORT_KIND, contract_metadata

from .artifacts import read_json
from .merge_gate import merge_gate_verdict, verification_state
from .risk import summarize_risk
from .summarize import summarize_diff


def compose_review_report(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    if "summary" in run_artifact and isinstance(run_artifact["summary"], Mapping):
        return dict(run_artifact)

    verification = verification_state(run_artifact)
    diff = summarize_diff(run_artifact)
    risk = summarize_risk(diff, verification)
    gate = merge_gate_verdict(run_artifact, risk_summary=risk)
    plan = run_artifact.get("plan", {})
    supporting_checks = []
    if isinstance(plan, Mapping):
        supporting_checks = list(plan.get("required_checks", []))

    return {
        "contract": contract_metadata(REVIEW_REPORT_KIND),
        "run_id": run_artifact.get("run_id") or run_artifact.get("id") or "unknown-run",
        "task_id": run_artifact.get("task_id") or run_artifact.get("task") or None,
        "summary": {
            "diff": diff,
            "risk": risk,
            "verification": verification,
            "merge_gate": gate,
        },
        "supporting_checks": supporting_checks,
    }


def compose_review_report_from_path(path: Path) -> dict[str, Any]:
    selected_path = path
    if path.name == "run_ledger.json":
        sibling = path.with_name("run_artifact.json")
        if sibling.exists():
            selected_path = sibling
    artifact = read_json(selected_path)
    report = compose_review_report(artifact)
    report["artifact_path"] = str(path)
    return report
