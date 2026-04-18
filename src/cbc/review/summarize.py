from __future__ import annotations

from typing import Any, Mapping

from cbc.models import ReviewReport, RunLedger
from cbc.roles.reviewer import build_review_report


def summarize_run(ledger: RunLedger) -> ReviewReport:
    return build_review_report(ledger)


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

    return {
        "total_files": len(files),
        "files": files,
    }
