from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from cbc.config import AppConfig, PathsConfig
from cbc.intake.dynamic import build_dynamic_task, ensure_dynamic_oracle, guess_scope_candidates
from cbc.intake.toolchains import detect_toolchain
from cbc.main import app
from cbc.models import AdapterRunResult, FileWrite, ModelResponse, VerificationVerdict


ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def build_test_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        paths=PathsConfig(
            root=ROOT,
            artifacts_dir=tmp_path / "artifacts",
            reports_dir=tmp_path / "reports",
            prompts_dir=ROOT / "prompts",
            benchmark_config_dir=ROOT / "benchmark-configs",
            storage_db=tmp_path / "artifacts" / "cbc.sqlite3",
        )
    )


def test_detect_toolchain_combines_python_and_node_defaults(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"lint": "eslint .", "typecheck": "tsc --noEmit"}}),
        encoding="utf-8",
    )

    detection = detect_toolchain(tmp_path)

    assert detection.languages == ["javascript", "python"]
    assert detection.verify_commands == ["npm test", "pytest -q"]
    assert detection.lint_command == "npm run lint"
    assert detection.typecheck_command == "npm run typecheck"


def test_build_dynamic_task_respects_verify_override(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_app.py").write_text("def test_value():\n    assert True\n", encoding="utf-8")

    task = build_dynamic_task("Fix app value", tmp_path, verify_cmd="python3 -m pytest -q")

    assert task.metadata["dynamic_task"] is True
    assert task.oracles[0].command == "python3 -m pytest -q"
    assert task.required_checks == ["oracle-1"]


def test_guess_scope_candidates_prefers_rg_keyword_hits(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def status_badge():\n    return 'broken'\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("status badge design notes\n", encoding="utf-8")

    monkeypatch.setattr("cbc.intake.dynamic.shutil.which", lambda _: "/usr/bin/rg")

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if cmd[:2] == ["rg", "--files"]:
            return subprocess.CompletedProcess(cmd, 0, "app.py\nnotes.txt\n", "")
        if cmd[:3] == ["rg", "-l", "-i"]:
            keyword = cmd[3]
            if keyword in {"status", "badge"}:
                return subprocess.CompletedProcess(cmd, 0, "app.py\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("cbc.intake.dynamic.subprocess.run", fake_run)

    candidates = guess_scope_candidates(
        "Fix the status badge renderer",
        tmp_path,
        detection=detect_toolchain(tmp_path),
        limit=2,
    )

    assert candidates[0] == "app.py"


def test_ensure_dynamic_oracle_persists_generated_script(monkeypatch, tmp_path: Path) -> None:
    task = build_dynamic_task("Add a health endpoint", tmp_path, verify_cmd=None)
    task = task.model_copy(update={"oracles": [], "required_checks": []})

    class FakeAdapter:
        name = "codex"

        def run(self, **_: object) -> AdapterRunResult:
            return AdapterRunResult(
                response=ModelResponse(
                    summary="generated oracle",
                    claimed_success=True,
                    writes=[
                        FileWrite(
                            path="generated_verify.sh",
                            content="#!/usr/bin/env bash\nexit 0\n",
                            executable=True,
                        )
                    ],
                )
            )

    monkeypatch.setattr("cbc.intake.dynamic.load_adapter", lambda *args, **kwargs: FakeAdapter())

    updated = ensure_dynamic_oracle(task, config=build_test_config(tmp_path))

    assert updated.required_checks == ["generated-oracle"]
    generated_path = Path(str(updated.metadata["generated_oracle"]))
    assert generated_path.exists()
    assert os.access(generated_path, os.X_OK)
    assert updated.oracles[0].command == str(generated_path)


def test_solve_command_emits_json_artifact(monkeypatch, tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "run_artifact.json").write_text(json.dumps({"run_id": "solve-123"}), encoding="utf-8")

    monkeypatch.setattr("cbc.main.build_dynamic_task", lambda *args, **kwargs: SimpleNamespace(oracles=[object()]))
    monkeypatch.setattr("cbc.main.ensure_dynamic_oracle", lambda task, **kwargs: task)
    monkeypatch.setattr(
        "cbc.main.run_task",
        lambda *args, **kwargs: SimpleNamespace(artifact_dir=artifact_dir),
    )

    result = runner.invoke(app, ["solve", "Add a health endpoint", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["run_id"] == "solve-123"


def test_run_command_stream_emits_ndjson_events(monkeypatch, tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "run_artifact.json").write_text(json.dumps({"run_id": "run-123"}), encoding="utf-8")

    def fake_run_task(task, **kwargs):
        event_sink = kwargs["event_sink"]
        event_sink({"type": "attempt.started", "attempt": 1})
        return SimpleNamespace(
            artifact_dir=artifact_dir,
            run_id="run-123",
            task_id="demo-task",
            mode="treatment",
            verdict=VerificationVerdict.VERIFIED,
            unsafe_claims=0,
            attempts=[object()],
            final_summary="verified",
            workspace_dir=tmp_path / "workspace",
        )

    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr("cbc.main.run_task", fake_run_task)

    result = runner.invoke(app, ["run", "fixtures/oracle_tasks/calculator_bug/task.yaml", "--stream", "--json"])

    assert result.exit_code == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert json.loads(lines[0]) == {"attempt": 1, "type": "attempt.started"}
    artifact_payload = json.loads("\n".join(lines[1:]))
    assert artifact_payload["run_id"] == "run-123"


def test_trends_command_emits_json_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "cbc.main.load_recent_runs",
        lambda path, limit=20: [
            {
                "run_id": "run-1",
                "task_id": "task-a",
                "mode": "treatment",
                "verdict": "VERIFIED",
                "unsafe_claims": 0,
                "elapsed_seconds": 2.0,
                "total_tokens": 100,
                "estimated_cost_usd": 0.01,
            },
            {
                "run_id": "run-2",
                "task_id": "task-b",
                "mode": "treatment",
                "verdict": "FALSIFIED",
                "unsafe_claims": 1,
                "elapsed_seconds": 4.0,
                "total_tokens": 300,
                "estimated_cost_usd": 0.03,
            },
        ],
    )

    result = runner.invoke(app, ["trends", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["count"] == 2
    assert payload["verified_success_rate"] == 0.5
    assert payload["unsafe_claim_rate"] == 0.5
    assert payload["average_total_tokens"] == 200
    assert payload["average_estimated_cost_usd"] == 0.02
