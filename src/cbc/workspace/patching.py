from __future__ import annotations

import stat
from pathlib import Path

from cbc.models import FileWrite
from cbc.workspace.scope_guard import assert_allowed_path


def normalize_write_path(workspace: Path, path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate
    try:
        return candidate.resolve().relative_to(workspace.resolve())
    except ValueError as exc:
        raise ValueError(f"write to {path!r} is outside the staged workspace") from exc


def apply_writes(workspace: Path, writes: list[FileWrite], allowed_files: list[str]) -> list[str]:
    changed: list[str] = []
    for write in writes:
        relative_path = normalize_write_path(workspace, write.path)
        normalized = relative_path.as_posix()
        assert_allowed_path(normalized, allowed_files)
        target = workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(write.content, encoding="utf-8")
        if write.executable:
            target.chmod(target.stat().st_mode | stat.S_IXUSR)
        changed.append(normalized)
    return changed
