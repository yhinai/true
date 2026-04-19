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


def test_run_json_mode_suppresses_spinner(tmp_path: Path, monkeypatch):
    """--json output must not contain Rich spinner escape codes."""
    from pathlib import Path as _P

    def fake_run_task(*args, **kwargs):
        class _R:
            def model_dump(self, *a, **kw):
                return {"verdict": "VERIFIED", "status": "VERIFIED"}
        return _R()

    monkeypatch.setattr("cbc.main.run_task", fake_run_task)
    try:
        monkeypatch.setattr(
            "cbc.main.load_task",
            lambda p: type("T", (), {"task_id": "t1", "root": _P(p).parent, "title": "x", "workspace": _P(p).parent / "workspace"})(),
        )
    except AttributeError:
        pass

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(app, ["run", str(task_file), "--json"])
    # No Rich escape codes for spinner frames
    assert "\x1b[?25l" not in result.output  # cursor-hide
    assert "⠋" not in result.output and "⠙" not in result.output  # spinner glyphs


def _stub_benchmark_comparison() -> object:
    class _C:
        def model_dump(self, *a, **kw):
            return {"benchmark_verdict": "pass"}

    return _C()


def test_compare_json_suppresses_spinner(monkeypatch) -> None:
    monkeypatch.setattr(
        "cbc.main.run_local_benchmark",
        lambda path: _stub_benchmark_comparison(),
    )
    result = runner.invoke(app, ["compare", "--json"])
    assert "\x1b[?25l" not in result.output
    assert "⠋" not in result.output and "⠙" not in result.output


def test_controller_compare_json_suppresses_spinner(monkeypatch) -> None:
    monkeypatch.setattr(
        "cbc.main.run_local_controller_benchmark",
        lambda path: _stub_benchmark_comparison(),
    )
    result = runner.invoke(app, ["controller-compare", "--json"])
    assert "\x1b[?25l" not in result.output
    assert "⠋" not in result.output and "⠙" not in result.output


def test_poc_json_suppresses_spinner(monkeypatch) -> None:
    monkeypatch.setattr(
        "cbc.main.run_poc_comparison",
        lambda *a, **kw: _stub_benchmark_comparison(),
    )
    result = runner.invoke(app, ["poc", "--json", "--simulated"])
    assert "\x1b[?25l" not in result.output
    assert "⠋" not in result.output and "⠙" not in result.output


def test_solve_json_suppresses_spinner(tmp_path: Path, monkeypatch) -> None:
    def fake_run_task(*args, **kwargs):
        return _stub_ledger(tmp_path)

    monkeypatch.setattr("cbc.main.run_task", fake_run_task)
    monkeypatch.setattr(
        "cbc.main.build_dynamic_task",
        lambda prompt, cwd, verify_cmd=None, agent_name=None: type(
            "T", (), {"task_id": "t1", "oracles": ["x"]}
        )(),
    )
    monkeypatch.setattr(
        "cbc.main.ensure_dynamic_oracle",
        lambda task, agent_name=None: task,
    )
    result = runner.invoke(app, ["solve", "do a thing", "--json"])
    assert "\x1b[?25l" not in result.output
    assert "⠋" not in result.output and "⠙" not in result.output


def test_run_accepts_scoring_weights_flag(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_task(task, **kwargs):
        captured.update(kwargs)
        return _stub_ledger(tmp_path)

    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr("cbc.main.run_task", fake_run_task)

    weights_yaml = tmp_path / "w.yaml"
    weights_yaml.write_text("verified_bonus: 999\n")
    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(
        app,
        ["run", str(task_file), "--scoring-weights", str(weights_yaml), "--json"],
    )
    assert "scoring_weights" in captured, f"kwarg missing; output: {result.output}"
    assert captured["scoring_weights"].verified_bonus == 999
