from __future__ import annotations

from pathlib import Path

import pytest

from cbc.intake.normalize import load_task


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("task_path", "expected_workspace", "expected_checks", "expected_oracle_name", "expected_oracle_kind"),
    [
        (
            REPO_ROOT / "fixtures/oracle_tasks/title_case_bug_codex/task.yaml",
            REPO_ROOT / "fixtures/oracle_tasks/title_case_bug/workspace",
            ["pytest"],
            "pytest",
            "pytest",
        ),
        (
            REPO_ROOT / "fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml",
            REPO_ROOT / "fixtures/oracle_tasks/slug_shell_bug/workspace",
            ["shell-oracle"],
            "shell-oracle",
            "shell",
        ),
        (
            REPO_ROOT / "fixtures/oracle_tasks/live_codex_calculator/task.yaml",
            REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/workspace",
            ["pytest"],
            "pytest",
            "pytest",
        ),
    ],
)
def test_live_codex_task_specs_load_correctly(
    task_path: Path,
    expected_workspace: Path,
    expected_checks: list[str],
    expected_oracle_name: str,
    expected_oracle_kind: str,
) -> None:
    task = load_task(task_path)

    assert task.adapter == "codex"
    assert task.replay_file is None
    assert task.workspace == expected_workspace.resolve()
    assert task.required_checks == expected_checks
    assert len(task.oracles) == 1
    assert task.oracles[0].name == expected_oracle_name
    assert task.oracles[0].kind == expected_oracle_kind
    assert task.codex.model == "gpt-5.4"
    assert task.codex.sandbox == "workspace-write"
    assert task.codex.skip_git_repo_check is True
    assert task.codex.dangerously_bypass_approvals is False
