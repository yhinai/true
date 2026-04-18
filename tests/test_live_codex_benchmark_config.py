from __future__ import annotations

from pathlib import Path

from cbc.benchmark.local_runner import load_task_paths_from_config


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_live_codex_subset_config_resolves_all_live_task_specs() -> None:
    task_paths = load_task_paths_from_config(REPO_ROOT / "benchmark-configs/live_codex_subset.yaml")

    assert task_paths == [
        (REPO_ROOT / "fixtures/oracle_tasks/calculator_bug_codex/task.yaml").resolve(),
        (REPO_ROOT / "fixtures/oracle_tasks/title_case_bug_codex/task.yaml").resolve(),
        (REPO_ROOT / "fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml").resolve(),
    ]
