from __future__ import annotations

from pathlib import Path

from cbc.benchmark.compare import run_comparison
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


def test_comparison_shows_treatment_lift(tmp_path: Path) -> None:
    task_paths = [
        REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml",
        REPO_ROOT / "fixtures/oracle_tasks/title_case_bug/task.yaml",
        REPO_ROOT / "fixtures/oracle_tasks/slug_shell_bug/task.yaml",
    ]
    comparison = run_comparison(
        task_paths=task_paths,
        config_path=REPO_ROOT / "benchmark-configs/curated_subset.yaml",
        config=build_test_config(tmp_path),
    )

    assert comparison.treatment_metrics.verified_success_rate > comparison.baseline_metrics.verified_success_rate
    assert (comparison.report_dir / "comparison.md").exists()
