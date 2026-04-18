from __future__ import annotations

from typing import Any, Mapping

from .artifacts import pick_first

HIGH_RISK_PATH_MARKERS = (
    "src/cbc/verify",
    "src/cbc/workspace",
    ".github/workflows",
    "pyproject.toml",
    "requirements",
)


def _extract_changed_files(run_artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    diff_obj = pick_first(run_artifact, "diff", "patch", "changes", "change_set")
    candidates: Any = None
    if isinstance(diff_obj, Mapping):
        candidates = pick_first(diff_obj, "files", "changed_files")
    if candidates is None:
        candidates = pick_first(run_artifact, "changed_files", "files_changed", "files")
    if not isinstance(candidates, list):
        return []

    normalized: list[dict[str, Any]] = []
    for entry in candidates:
        if isinstance(entry, str):
            normalized.append({"path": entry, "additions": 0, "deletions": 0, "change_type": "modified"})
            continue
        if not isinstance(entry, Mapping):
            continue
        path = (
            entry.get("path")
            or entry.get("file")
            or entry.get("filename")
            or entry.get("name")
            or "unknown"
        )
        normalized.append(
            {
                "path": str(path),
                "additions": int(entry.get("additions", entry.get("insertions", 0)) or 0),
                "deletions": int(entry.get("deletions", entry.get("removals", 0)) or 0),
                "change_type": str(entry.get("change_type", entry.get("status", "modified"))),
            }
        )
    return normalized


def summarize_diff(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    files = _extract_changed_files(run_artifact)
    additions = sum(file_entry["additions"] for file_entry in files)
    deletions = sum(file_entry["deletions"] for file_entry in files)
    high_risk_files = [
        file_entry["path"]
        for file_entry in files
        if any(marker in file_entry["path"] for marker in HIGH_RISK_PATH_MARKERS)
    ]
    return {
        "file_count": len(files),
        "total_additions": additions,
        "total_deletions": deletions,
        "high_risk_files": high_risk_files,
        "files": files,
    }
