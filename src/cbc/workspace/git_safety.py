from __future__ import annotations

from pathlib import Path


def describe_workspace_safety(source: Path, staged: Path) -> str:
    return (
        f"Source workspace {source} was copied into staged workspace {staged}. "
        "All edits are confined to the staged copy."
    )
