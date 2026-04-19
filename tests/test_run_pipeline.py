from __future__ import annotations

from pathlib import Path
import shutil

from cbc.config import AppConfig, PathsConfig, RetryConfig
from cbc.controller.orchestrator import resolve_codex_config, review_workspace, run_task
from cbc.intake.normalize import load_task
from cbc.review.ci import build_ci_report
from cbc.review.report import compose_review_report_from_path
from cbc.models import VerificationVerdict
from cbc.api.store import get_run, list_runs


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_test_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        paths=PathsConfig(
            root=REPO_ROOT,
            artifacts_dir=tmp_path / "artifacts",
            reports_dir=tmp_path / "reports",
            prompts_dir=REPO_ROOT / "prompts",
            benchmark_config_dir=REPO_ROOT / "benchmark-configs",
            storage_db=tmp_path / "artifacts" / "cbc.sqlite3",
        ),
        retry=RetryConfig(max_attempts=2),
    )


def test_treatment_retries_to_verified(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml")
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 2
    assert ledger.unsafe_claims == 1
    assert (ledger.artifact_dir / "proof_card.md").exists()
    assert (ledger.artifact_dir / "run_artifact.json").exists()
    assert (ledger.artifact_dir / "review_report.json").exists()
    assert (ledger.artifact_dir / "merge_gate.json").exists()
    assert (ledger.artifact_dir / "ci_report.json").exists()
    assert (ledger.artifact_dir / "explorer_artifact.json").exists()

    review_report = compose_review_report_from_path(ledger.artifact_dir / "run_ledger.json")
    assert review_report["run_id"] == ledger.run_id
    assert review_report["summary"]["verification"]["state"] == "VERIFIED"
    assert review_report["summary"]["diff"]["total_files"] == 1

    runs = list_runs(tmp_path / "artifacts", limit=10)
    assert [run["run_id"] for run in runs] == [ledger.run_id]

    stored = get_run(tmp_path / "artifacts", ledger.run_id)
    assert stored is not None
    assert stored["summary"]["merge_gate"]["verdict"] == "UNSAFE"


def test_baseline_stops_after_first_failure(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml")
    ledger = run_task(task, mode="baseline", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.FALSIFIED
    assert len(ledger.attempts) == 1


def test_live_codex_task_spec_loads_without_replay_file() -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug_codex/task.yaml")

    assert task.adapter == "codex"
    assert task.replay_file is None
    assert task.workspace == (REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/workspace").resolve()

def test_task_codex_config_overrides_live_lane_defaults(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug_codex/task.yaml")
    config = build_test_config(tmp_path)
    config.codex.default_model = "fallback-model"
    config.codex.sandbox = "read-only"
    config.codex.config_overrides = ['foo="bar"']
    config.codex.dangerously_bypass_approvals = True

    resolved = resolve_codex_config(task, config)

    assert resolved.default_model == "gpt-5.4"
    assert resolved.sandbox == "workspace-write"
    assert resolved.config_overrides == ['foo="bar"', 'model_reasoning_effort="medium"']
    assert resolved.skip_git_repo_check is True
    assert resolved.dangerously_bypass_approvals is False


def test_review_workspace_builds_ci_ready_artifacts(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml")
    reviewed_workspace = tmp_path / "reviewed"
    shutil.copytree(task.workspace, reviewed_workspace)
    (reviewed_workspace / "calculator.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )

    ledger = review_workspace(task, reviewed_workspace, config=build_test_config(tmp_path))

    assert ledger.mode == "review"
    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 1
    assert (ledger.artifact_dir / "ci_report.json").exists()

    review_report = compose_review_report_from_path(ledger.artifact_dir / "run_ledger.json")
    assert review_report["summary"]["diff"]["total_files"] == 1
    assert review_report["summary"]["merge_gate"]["verdict"] == "APPROVE"

    ci_report = build_ci_report(review_report)
    assert ci_report["exit_code"] == 0


def test_property_task_generates_regression_artifact_on_retry(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/slugify_property_regression/task.yaml")
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 2

    first_attempt_checks = {check.name: check for check in ledger.attempts[0].verification.checks}
    assert first_attempt_checks["hypothesis"].status.value == "failed"

    regression_artifact = first_attempt_checks["hypothesis"].details["regression_test_artifact"]
    counterexample_artifact = first_attempt_checks["hypothesis"].details["counterexample_artifact"]
    assert Path(regression_artifact).exists()
    assert Path(counterexample_artifact).exists()

    run_artifact = compose_review_report_from_path(ledger.artifact_dir / "run_ledger.json")
    assert run_artifact["summary"]["verification"]["state"] == "VERIFIED"
    raw_run_artifact = (ledger.artifact_dir / "run_artifact.json").read_text(encoding="utf-8")
    assert "generated_test_artifacts" in raw_run_artifact
    assert '"explorer"' in raw_run_artifact
    assert '"policy"' in raw_run_artifact


def test_multi_file_structural_task_retries_to_verified(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/checkout_tax_propagation/task.yaml")
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 2

    first_attempt_checks = {check.name: check for check in ledger.attempts[0].verification.checks}
    assert first_attempt_checks["structural"].status.value == "failed"
    assert first_attempt_checks["pytest"].status.value == "failed"

    final_checks = {check.name: check for check in ledger.attempts[-1].verification.checks}
    assert final_checks["structural"].status.value == "passed"
    assert final_checks["pytest"].status.value == "passed"


def test_second_property_task_generates_regression_artifact(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/price_format_property_regression/task.yaml")
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 2

    first_attempt_checks = {check.name: check for check in ledger.attempts[0].verification.checks}
    assert first_attempt_checks["hypothesis"].status.value == "failed"
    assert Path(first_attempt_checks["hypothesis"].details["counterexample_artifact"]).exists()
    assert Path(first_attempt_checks["hypothesis"].details["regression_test_artifact"]).exists()


def test_non_python_js_task_retries_to_verified(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/status_badge_js_contract/task.yaml")
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.attempts) == 2
    assert ledger.attempts[0].verification.checks[0].name == "node-oracle"
