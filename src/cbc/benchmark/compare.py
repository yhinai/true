from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from cbc.benchmark.baseline import run_baseline
from cbc.benchmark.metrics import compute_metrics
from cbc.benchmark.reports import save_benchmark_report
from cbc.benchmark.treatment import run_treatment
from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.intake.normalize import load_task
from cbc.models import BenchmarkComparison
from cbc.storage.artifacts import create_artifact_dir
from cbc.storage.benchmark_results import save_benchmark


def run_comparison(*, task_paths: list[Path], config_path: Path, config: AppConfig = DEFAULT_CONFIG) -> BenchmarkComparison:
    baseline_results = []
    treatment_results = []
    for task_path in task_paths:
        task = load_task(task_path)
        baseline_results.append(run_baseline(task, config))
        treatment_results.append(run_treatment(task, config))

    baseline_metrics = compute_metrics(baseline_results)
    treatment_metrics = compute_metrics(treatment_results)
    report_dir = create_artifact_dir(config.paths.reports_dir, "benchmarks")
    comparison = BenchmarkComparison(
        benchmark_id=uuid4().hex[:12],
        config_path=config_path,
        task_results=baseline_results + treatment_results,
        baseline_metrics=baseline_metrics,
        treatment_metrics=treatment_metrics,
        delta_verified_success_rate=treatment_metrics.verified_success_rate - baseline_metrics.verified_success_rate,
        delta_unsafe_claim_rate=baseline_metrics.unsafe_claim_rate - treatment_metrics.unsafe_claim_rate,
        report_dir=report_dir,
    )
    save_benchmark_report(comparison)
    save_benchmark(config.paths.storage_db, comparison)
    return comparison
