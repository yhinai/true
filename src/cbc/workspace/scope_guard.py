from __future__ import annotations

from pathlib import Path


def assert_allowed_path(relative_path: str, allowed_files: list[str]) -> None:
    if not allowed_files:
        return
    normalized = Path(relative_path).as_posix()
    if normalized not in {Path(item).as_posix() for item in allowed_files}:
        raise ValueError(f"write to {relative_path!r} is outside the allowed scope")
