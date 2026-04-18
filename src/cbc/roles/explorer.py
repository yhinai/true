from __future__ import annotations

from pathlib import Path


def list_python_files(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*.py"))
