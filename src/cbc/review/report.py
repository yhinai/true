from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .artifacts import read_json
from .merge_gate import merge_gate_verdict, verification_state
from .risk import summarize_risk
from .summarize import summarize_diff


def compose_review_report(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    verification = verification_state(run_artifact)
    diff = summarize_diff(run_artifact)
    risk = summarize_risk(diff, verification)
    gate = merge_gate_verdict(run_artifact, risk_summary=risk)

    return {
        "run_id": run_artifact.get("run_id") or run_artifact.get("id") or "unknown-run",
        "task_id": run_artifact.get("task_id") or run_artifact.get("task") or None,
        "summary": {
            "diff": diff,
            "risk": risk,
            "verification": verification,
            "merge_gate": gate,
        },
    }


def compose_review_report_from_path(path: Path) -> dict[str, Any]:
    artifact = read_json(path)
    report = compose_review_report(artifact)
    report["artifact_path"] = str(path)
    return report
