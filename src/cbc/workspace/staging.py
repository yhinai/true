from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkspaceLease:
    root: Path
    path: Path

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def create_workspace_lease(source: Path) -> WorkspaceLease:
    temp_dir = Path(tempfile.mkdtemp(prefix="cbc-workspace-"))
    destination = temp_dir / source.name
    shutil.copytree(source, destination)
    return WorkspaceLease(root=temp_dir, path=destination)


def stage_workspace(source: Path) -> Path:
    return create_workspace_lease(source).path
