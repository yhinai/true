from __future__ import annotations

from pathlib import Path

from cbc.workspace.staging import stage_workspace


def create_staged_worktree(source: Path) -> Path:
    return stage_workspace(source)
