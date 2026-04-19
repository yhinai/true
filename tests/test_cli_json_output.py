from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from rich.console import Console
from typer.testing import CliRunner

from cbc.main import app
from cbc.models import BenchmarkComparison, BenchmarkMetrics, BenchmarkTaskResult, VerificationVerdict


runner = CliRunner()


def test_run_command_emits_json_artifact(monkeypatch, tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "run_artifact.json").write_text(
        json.dumps({"run_id": "run-123", "controller": {"mode": "gearbox"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr(
        "cbc.main.run_task",
        lambda task, mode="treatment", controller_mode="sequential": SimpleNamespace(artifact_dir=artifact_dir),
    )

    result = runner.invoke(app, ["run", "fixtures/oracle_tasks/calculator_bug/task.yaml", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_id"] == "run-123"
    assert payload["controller"]["mode"] == "gearbox"


def test_compare_command_emits_json_payload(monkeypatch, tmp_path: Path) -> None:
    comparison = BenchmarkComparison(
        benchmark_id="bench-123",
        config_path=tmp_path / "config.yaml",
        task_results=[
            BenchmarkTaskResult(
                task_id="task-a",
                mode="baseline",
                verdict=VerificationVerdict.FALSIFIED,
                verified_success=False,
                unsafe_claims=1,
                retries=0,
                elapsed_seconds=1.0,
                artifact_dir=tmp_path / "artifacts" / "run-a",
            )
        ],
        baseline_metrics=BenchmarkMetrics(
            verified_success_rate=0.0,
            unsafe_claim_rate=1.0,
            average_retries=0.0,
            average_elapsed_seconds=1.0,
        ),
        treatment_metrics=BenchmarkMetrics(
            verified_success_rate=1.0,
            unsafe_claim_rate=0.0,
            average_retries=1.0,
            average_elapsed_seconds=2.0,
        ),
        delta_verified_success_rate=1.0,
        delta_unsafe_claim_rate=1.0,
        report_dir=tmp_path / "reports" / "bench-123",
    )
    monkeypatch.setattr("cbc.main.run_local_benchmark", lambda config_path: comparison)

    result = runner.invoke(app, ["compare", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["benchmark_id"] == "bench-123"
    assert payload["treatment_metrics"]["verified_success_rate"] == 1.0


def test_poc_command_emits_json_payload(monkeypatch, tmp_path: Path) -> None:
    payload = {
        "poc_id": "poc-123",
        "sample_size": 2,
        "pairwise_summaries": [
            {
                "left_arm": "cbc_treatment",
                "right_arm": "raw_codex",
                "verified_success_rate_delta": 0.5,
            }
        ],
    }
    monkeypatch.setattr(
        "cbc.main.run_poc_comparison",
        lambda *args, **kwargs: SimpleNamespace(model_dump=lambda mode="json": payload),
    )

    result = runner.invoke(app, ["poc", "--json"])

    assert result.exit_code == 0
    poc_payload = json.loads(result.stdout)
    assert poc_payload["poc_id"] == "poc-123"
    assert poc_payload["pairwise_summaries"][0]["verified_success_rate_delta"] == 0.5


def test_poc_command_prints_pairwise_scoreboard(monkeypatch, tmp_path: Path) -> None:
    metric = SimpleNamespace(
        total_runs=2,
        verified_success_rate=0.5,
        verified_success_ci=SimpleNamespace(low=0.1, high=0.9),
        unsafe_claim_rate=0.0,
        unsafe_claim_ci=SimpleNamespace(low=0.0, high=0.5),
        average_retries=0.5,
        average_elapsed_seconds=1.2,
        average_changed_files=1.0,
    )
    pairwise = SimpleNamespace(
        left_arm=SimpleNamespace(value="cbc_treatment"),
        right_arm=SimpleNamespace(value="raw_codex"),
        total_pairs=2,
        verified_success_rate_delta=0.5,
        verified_success_rate_ci=SimpleNamespace(low=0.0, high=1.0),
        verified_success_outcomes=SimpleNamespace(wins=1, losses=0, ties=1),
        unsafe_claim_rate_reduction=0.5,
        unsafe_claim_rate_reduction_ci=SimpleNamespace(low=0.0, high=1.0),
        safer_outcomes=SimpleNamespace(wins=1, losses=0, ties=1),
    )
    comparison = SimpleNamespace(
        raw_codex_metrics=metric,
        cbc_baseline_metrics=metric,
        cbc_treatment_metrics=metric,
        pairwise_summaries=[pairwise],
        sampled_tasks=[tmp_path / "fixtures" / "demo_task" / "task.yaml"],
        report_dir=tmp_path / "reports" / "poc-123",
    )
    monkeypatch.setattr("cbc.main.console", Console(width=200, force_terminal=False, color_system=None))
    monkeypatch.setattr("cbc.main.run_poc_comparison", lambda *args, **kwargs: comparison)

    result = runner.invoke(app, ["poc"])

    assert result.exit_code == 0
    assert "POC Comparison" in result.stdout
    assert "POC Pairwise Scoreboard" in result.stdout
    assert "cbc_treatment vs raw_codex" in result.stdout
    assert "Unsafe Reduction" in result.stdout
    assert "0.5" in result.stdout
    assert "Sampled tasks: demo_task" in result.stdout


def test_review_and_ci_artifact_commands_emit_json(tmp_path: Path) -> None:
    artifact_path = tmp_path / "run_artifact.json"
    artifact_path.write_text(
        json.dumps(
            {
                "run_id": "run-123",
                "task_id": "task-a",
                "diff": {"total_files": 1, "files": [{"path": "calculator.py", "additions": 1, "deletions": 1}]},
                "verification": {"status": "VERIFIED", "checks": [{"name": "pytest", "status": "passed"}]},
            }
        ),
        encoding="utf-8",
    )

    review_result = runner.invoke(app, ["review-artifact", str(artifact_path), "--json"])
    assert review_result.exit_code == 0
    review_payload = json.loads(review_result.stdout)
    assert review_payload["run_id"] == "run-123"
    assert review_payload["summary"]["merge_gate"]["verdict"] == "APPROVE"

    ci_result = runner.invoke(app, ["ci-artifact", str(artifact_path), "--json"])
    assert ci_result.exit_code == 0
    ci_payload = json.loads(ci_result.stdout)
    assert ci_payload["merge_gate_verdict"] == "APPROVE"
    assert ci_payload["verification_state"] == "VERIFIED"


def test_review_workspace_command_emits_json(monkeypatch, tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    monkeypatch.setattr("cbc.main.load_task", lambda path: object())
    monkeypatch.setattr(
        "cbc.main.review_workspace",
        lambda task, workspace_path: SimpleNamespace(artifact_dir=artifact_dir),
    )
    monkeypatch.setattr(
        "cbc.main.compose_review_report_from_path",
        lambda path: {
            "run_id": "review-123",
            "summary": {
                "verification": {"state": "VERIFIED"},
                "merge_gate": {"verdict": "APPROVE"},
            },
        },
    )

    result = runner.invoke(
        app,
        [
            "review-workspace",
            "fixtures/oracle_tasks/calculator_bug/task.yaml",
            str(tmp_path / "workspace"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_id"] == "review-123"
    assert payload["summary"]["merge_gate"]["verdict"] == "APPROVE"
