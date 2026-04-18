from __future__ import annotations

from pathlib import Path


def checkpoint_name(attempt: int, workspace: Path) -> str:
    return f"attempt-{attempt}@{workspace.name}"
