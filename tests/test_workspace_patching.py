from __future__ import annotations

from pathlib import Path

import pytest

from cbc.models import FileWrite
from cbc.workspace.patching import apply_writes


def test_apply_writes_accepts_absolute_paths_inside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "calculator.py"

    changed = apply_writes(
        workspace,
        [FileWrite(path=str(target), content="def add(a, b):\n    return a + b\n")],
        ["calculator.py"],
    )

    assert changed == ["calculator.py"]
    assert target.read_text(encoding="utf-8") == "def add(a, b):\n    return a + b\n"


def test_apply_writes_rejects_absolute_paths_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.py"

    with pytest.raises(ValueError, match="outside the staged workspace"):
        apply_writes(
            workspace,
            [FileWrite(path=str(outside), content="print('nope')\n")],
            ["outside.py"],
        )
