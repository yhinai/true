from __future__ import annotations

from typing import Any, Mapping

from cbc.models import ReviewReport, RunLedger


def summarize_run(ledger: RunLedger) -> ReviewReport:
    from cbc.review.report import compose_review_report

    report = compose_review_report(ledger.model_dump(mode="json"))
    return ReviewReport(
        verdict=report["summary"]["merge_gate"]["verdict"],
        summary=f"verification={report['summary']['verification']['state']}, risk={report['summary']['risk']['risk_level']}",
        risks=report["summary"]["risk"]["reasons"],
        supporting_checks=report.get("supporting_checks", []),
    )


def summarize_diff(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    diff = run_artifact.get("diff")
    files: list[dict[str, Any]] = []
    if isinstance(diff, dict) and isinstance(diff.get("files"), list):
        for file_entry in diff["files"]:
            if isinstance(file_entry, dict):
                files.append(file_entry)

    changed_files = run_artifact.get("changed_files")
    if isinstance(changed_files, list):
        for path in changed_files:
            if isinstance(path, str):
                files.append({"path": path, "status": "modified", "additions": 0, "deletions": 0})

    attempts = run_artifact.get("attempts")
    if isinstance(attempts, list) and attempts:
        last_attempt = attempts[-1]
        if isinstance(last_attempt, Mapping):
            verification = last_attempt.get("verification")
            if isinstance(verification, Mapping):
                for path in verification.get("changed_files", []):
                    if isinstance(path, str):
                        files.append({"path": path, "status": "modified", "additions": 0, "deletions": 0})

    return {
        "total_files": len({entry["path"] for entry in files if "path" in entry}),
        "files": files,
    }
