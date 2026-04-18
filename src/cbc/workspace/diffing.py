from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path


def summarize_workspace_diff(
    source: Path,
    staged: Path,
    *,
    changed_files: list[str] | None = None,
) -> dict[str, object]:
    candidates = set(changed_files or [])
    if not candidates:
        candidates = _discover_changed_files(source, staged)

    files: list[dict[str, object]] = []
    for relative_path in sorted(candidates):
        before = source / relative_path
        after = staged / relative_path
        if before.is_dir() or after.is_dir():
            continue

        before_text = _read_text(before) if before.exists() else ""
        after_text = _read_text(after) if after.exists() else ""
        if before.exists() and after.exists() and before_text == after_text:
            continue

        additions, deletions = _count_line_changes(before_text, after_text)
        files.append(
            {
                "path": relative_path,
                "status": _status(before.exists(), after.exists()),
                "additions": additions,
                "deletions": deletions,
                "before_exists": before.exists(),
                "after_exists": after.exists(),
            }
        )

    return {
        "total_files": len(files),
        "files": files,
    }


def _discover_changed_files(source: Path, staged: Path) -> set[str]:
    source_files = {path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()}
    staged_files = {path.relative_to(staged).as_posix() for path in staged.rglob("*") if path.is_file()}
    return source_files | staged_files


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _count_line_changes(before: str, after: str) -> tuple[int, int]:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = SequenceMatcher(a=before_lines, b=after_lines)
    additions = 0
    deletions = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            deletions += i2 - i1
        if tag in {"replace", "insert"}:
            additions += j2 - j1
    return additions, deletions


def _status(before_exists: bool, after_exists: bool) -> str:
    if before_exists and after_exists:
        return "modified"
    if after_exists:
        return "added"
    return "deleted"
