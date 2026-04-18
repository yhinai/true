from __future__ import annotations

from pathlib import Path

from cbc.benchmark import local_runner
from cbc.benchmark.local_runner import apply_benchmark_config, load_benchmark_config
from cbc.config import AppConfig, CodexConfig, PathsConfig, RetryConfig
from cbc.models import BenchmarkComparison, BenchmarkMetrics


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_live_codex_config_resolves_all_live_task_specs_and_pins_runtime() -> None:
    benchmark_config = load_benchmark_config(REPO_ROOT / "benchmark-configs/live_codex.yaml")

    assert benchmark_config.task_paths == [
        (REPO_ROOT / "fixtures/oracle_tasks/calculator_bug_codex/task.yaml").resolve(),
        (REPO_ROOT / "fixtures/oracle_tasks/title_case_bug_codex/task.yaml").resolve(),
        (REPO_ROOT / "fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml").resolve(),
    ]
    assert benchmark_config.codex is not None
    assert benchmark_config.codex.executable == "codex"
    assert benchmark_config.codex.sandbox == "workspace-write"
    assert benchmark_config.codex.skip_git_repo_check is True
    assert benchmark_config.codex.dangerously_bypass_approvals is False


def test_apply_benchmark_config_merges_partial_codex_overrides() -> None:
    base_config = AppConfig(
        paths=PathsConfig(root=REPO_ROOT),
        retry=RetryConfig(max_attempts=2),
        codex=CodexConfig(
            executable="codex-custom",
            default_model="base-model",
            sandbox="read-only",
            skip_git_repo_check=True,
            dangerously_bypass_approvals=False,
        ),
    )
    benchmark_config = load_benchmark_config(REPO_ROOT / "benchmark-configs/live_codex.yaml")

    merged = apply_benchmark_config(base_config, benchmark_config)

    assert merged.codex.executable == "codex"
    assert merged.codex.default_model == "base-model"
    assert merged.codex.sandbox == "workspace-write"
    assert merged.codex.skip_git_repo_check is True
    assert merged.codex.dangerously_bypass_approvals is False


def test_run_local_benchmark_applies_codex_overrides_before_compare(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "live.yaml"
    config_path.write_text(
        "\n".join(
            [
                "tasks:",
                f"  - {(REPO_ROOT / 'fixtures/oracle_tasks/calculator_bug/task.yaml').resolve()}",
                "codex:",
                "  default_model: lane-model",
                "  sandbox: danger-full-access",
                "  skip_git_repo_check: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    base_config = AppConfig(
        paths=PathsConfig(
            root=REPO_ROOT,
            artifacts_dir=tmp_path / "artifacts",
            reports_dir=tmp_path / "reports",
            prompts_dir=REPO_ROOT / "prompts",
            benchmark_config_dir=REPO_ROOT / "benchmark-configs",
            storage_db=tmp_path / "artifacts" / "cbc.sqlite3",
        ),
        retry=RetryConfig(max_attempts=2),
        codex=CodexConfig(default_model="base-model", sandbox="workspace-write", skip_git_repo_check=True),
    )

    captured: dict[str, object] = {}

    def fake_run_comparison(*, task_paths, config_path, config):
        captured["task_paths"] = task_paths
        captured["config_path"] = config_path
        captured["config"] = config
        return BenchmarkComparison(
            benchmark_id="bench123",
            config_path=config_path,
            task_results=[],
            baseline_metrics=BenchmarkMetrics(
                verified_success_rate=0.0,
                unsafe_claim_rate=0.0,
                average_retries=0.0,
                average_elapsed_seconds=0.0,
            ),
            treatment_metrics=BenchmarkMetrics(
                verified_success_rate=0.0,
                unsafe_claim_rate=0.0,
                average_retries=0.0,
                average_elapsed_seconds=0.0,
            ),
            delta_verified_success_rate=0.0,
            delta_unsafe_claim_rate=0.0,
            report_dir=tmp_path / "reports" / "bench123",
        )

    monkeypatch.setattr(local_runner, "run_comparison", fake_run_comparison)

    local_runner.run_local_benchmark(config_path, config=base_config)

    assert captured["task_paths"] == [(REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml").resolve()]
    effective_config = captured["config"]
    assert isinstance(effective_config, AppConfig)
    assert effective_config.codex.default_model == "lane-model"
    assert effective_config.codex.sandbox == "danger-full-access"
    assert effective_config.codex.skip_git_repo_check is False
    assert effective_config.codex.dangerously_bypass_approvals is False
