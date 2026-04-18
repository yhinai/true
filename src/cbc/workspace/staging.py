from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


def stage_workspace(source: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="cbc-workspace-"))
    destination = temp_dir / source.name
    shutil.copytree(source, destination)
    return destination
