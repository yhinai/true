from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.intake.normalize import load_task
from cbc.roles.explorer import build_explorer_artifact


def test_explorer_identifies_targets_tests_and_related_files() -> None:
    task = load_task(ROOT / "fixtures/oracle_tasks/slugify_property_regression/task.yaml")

    artifact = build_explorer_artifact(task, task.workspace)

    assert artifact.likely_targets == ["slugify.py"]
    assert "test_slugify.py" in artifact.nearby_tests
    assert "property_checks.py" in artifact.related_files
    assert "python_files_scanned=3" in artifact.notes
