from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from cbc.main import app

runner = CliRunner()


def _stub_ledger(tmp_path: Path) -> SimpleNamespace:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(exist_ok=True)
    (artifact_dir / "run_artifact.json").write_text('{"verdict": "VERIFIED"}', encoding="utf-8")
    return SimpleNamespace(artifact_dir=artifact_dir)


def test_run_accepts_sandbox_local_flag(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_task(task, **kwargs):
        captured.update(kwargs)
        return _stub_ledger(tmp_path)

    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr("cbc.main.run_task", fake_run_task)

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(app, ["run", str(task_file), "--sandbox", "local", "--json"])
    assert "sandbox" in captured, f"sandbox kwarg missing; output: {result.output}"
    assert str(captured["sandbox"]).lower().endswith("local")


def test_run_accepts_sandbox_contree_flag(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_task(task, **kwargs):
        captured.update(kwargs)
        return _stub_ledger(tmp_path)

    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr("cbc.main.run_task", fake_run_task)

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(app, ["run", str(task_file), "--sandbox", "contree", "--json"])
    assert "sandbox" in captured, f"sandbox kwarg missing; output: {result.output}"
    assert str(captured["sandbox"]).lower().endswith("contree")


def test_run_rejects_invalid_sandbox_value(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr("cbc.main.run_task", lambda *a, **kw: _stub_ledger(tmp_path))

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(app, ["run", str(task_file), "--sandbox", "nonsense", "--json"])
    assert result.exit_code != 0
