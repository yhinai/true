"""Every fixtures/oracle_tasks/*/task.yaml must load into a valid TaskSpec."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "oracle_tasks"
TASK_YAMLS = sorted(p for p in FIXTURE_ROOT.glob("*/task.yaml") if p.is_file())


@pytest.mark.parametrize(
    "task_yaml",
    TASK_YAMLS,
    ids=[p.parent.name for p in TASK_YAMLS] or ["no-oracle-tasks"],
)
def test_task_yaml_parses(task_yaml: Path) -> None:
    from cbc.intake.normalize import load_task

    task = load_task(task_yaml)
    assert task.task_id, f"task.yaml at {task_yaml} has no task_id"
    assert task.title, f"task {task.task_id} has no title"
    assert task.oracles, f"task {task.task_id} has no oracles"
