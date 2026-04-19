from pathlib import Path

from cbc.prompts.program_loader import load_program


def test_returns_empty_when_nothing_exists(tmp_path: Path):
    result = load_program(task_dir=tmp_path, repo_root=tmp_path)
    assert result == ""


def test_returns_global_only(tmp_path: Path):
    repo_root = tmp_path / "repo"
    task_dir = tmp_path / "task"
    repo_root.mkdir()
    task_dir.mkdir()
    (repo_root / "program.md").write_text("GLOBAL RULES\n")

    result = load_program(task_dir=task_dir, repo_root=repo_root)
    assert result == "GLOBAL RULES"


def test_returns_per_task_only(tmp_path: Path):
    repo_root = tmp_path / "repo"
    task_dir = tmp_path / "task"
    repo_root.mkdir()
    task_dir.mkdir()
    (task_dir / "program.md").write_text("TASK RULES\n")

    result = load_program(task_dir=task_dir, repo_root=repo_root)
    assert result == "TASK RULES"


def test_stacks_global_then_per_task(tmp_path: Path):
    repo_root = tmp_path / "repo"
    task_dir = tmp_path / "task"
    repo_root.mkdir()
    task_dir.mkdir()
    (repo_root / "program.md").write_text("GLOBAL\n")
    (task_dir / "program.md").write_text("TASK\n")

    result = load_program(task_dir=task_dir, repo_root=repo_root)
    assert "GLOBAL" in result
    assert "TASK" in result
    assert "---" in result
    # Task comes second so it wins on conflict
    assert result.index("GLOBAL") < result.index("TASK")


def test_also_accepts_dot_cbc_global(tmp_path: Path):
    repo_root = tmp_path / "repo"
    task_dir = tmp_path / "task"
    repo_root.mkdir()
    task_dir.mkdir()
    (repo_root / ".cbc").mkdir()
    (repo_root / ".cbc" / "program.md").write_text("DOT CBC GLOBAL\n")

    result = load_program(task_dir=task_dir, repo_root=repo_root)
    assert result == "DOT CBC GLOBAL"
