from __future__ import annotations

from pathlib import Path

from cbc.benchmark.controller_compare import run_controller_comparison
from cbc.config import AppConfig, PathsConfig, RetryConfig


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


def test_controller_comparison_keeps_sequential_as_default_on_curated_subset(tmp_path: Path) -> None:
    comparison = run_controller_comparison(
        task_paths=[REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml"],
        config_path=REPO_ROOT / "benchmark-configs/controller_subset.yaml",
        config=build_test_config(tmp_path),
    )

    assert comparison.decision.recommended_controller == "sequential"
    assert comparison.decision.should_promote_to_default is False
    assert comparison.gearbox_metrics.average_model_calls > comparison.sequential_metrics.average_model_calls
    assert (comparison.report_dir / "comparison.json").exists()
