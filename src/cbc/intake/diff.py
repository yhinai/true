from __future__ import annotations

import subprocess
from pathlib import Path


def read_diff(workspace: Path) -> str:
    completed = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--", "."],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()
