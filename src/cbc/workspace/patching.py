from __future__ import annotations

import stat
from pathlib import Path

from cbc.models import FileWrite
from cbc.workspace.scope_guard import assert_allowed_path


def apply_writes(workspace: Path, writes: list[FileWrite], allowed_files: list[str]) -> list[str]:
    changed: list[str] = []
    for write in writes:
        assert_allowed_path(write.path, allowed_files)
        target = workspace / write.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(write.content, encoding="utf-8")
        if write.executable:
            target.chmod(target.stat().st_mode | stat.S_IXUSR)
        changed.append(Path(write.path).as_posix())
    return changed
