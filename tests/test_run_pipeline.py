from __future__ import annotations

from pathlib import Path

from cbc.config import AppConfig, PathsConfig, RetryConfig
from cbc.controller.orchestrator import run_task
from cbc.intake.normalize import load_task
from cbc.models import VerificationVerdict


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


def test_baseline_stops_after_first_failure(tmp_path: Path) -> None:
    task = load_task(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml")
    ledger = run_task(task, mode="baseline", config=build_test_config(tmp_path))

    assert ledger.verdict == VerificationVerdict.FALSIFIED
    assert len(ledger.attempts) == 1
