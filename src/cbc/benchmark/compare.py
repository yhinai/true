from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .baseline import run_baseline_suite
from .metrics import compare_metrics, summarize_results
from .reports import write_comparison_json, write_markdown_report
from .treatment import run_treatment_suite
from .types import BenchmarkComparison, TaskDefinition, utc_now_iso

TaskOrchestrator = Callable[..., object]


def _default_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def run_comparison(
    tasks: list[TaskDefinition],
    *,
    baseline_timeout_s: int = 30,
    treatment_timeout_s: int = 30,
    treatment_max_retries: int = 2,
    orchestrator: TaskOrchestrator | None = None,
    artifacts_root: Path = Path("artifacts"),
    reports_root: Path = Path("reports"),
    run_id: str | None = None,
) -> BenchmarkComparison:
    effective_run_id = run_id or _default_run_id()
    run_artifact_dir = artifacts_root / "benchmark" / effective_run_id
    baseline_artifact_dir = run_artifact_dir / "baseline"
    treatment_artifact_dir = run_artifact_dir / "treatment"

    baseline_results = run_baseline_suite(
        tasks=tasks,
        timeout_s=baseline_timeout_s,
        orchestrator=orchestrator,
        artifact_dir=baseline_artifact_dir,
    )
    treatment_results = run_treatment_suite(
        tasks=tasks,
        timeout_s=treatment_timeout_s,
        max_retries=treatment_max_retries,
        orchestrator=orchestrator,
        artifact_dir=treatment_artifact_dir,
    )

    baseline_metrics = summarize_results(baseline_results)
    treatment_metrics = summarize_results(treatment_results)
    deltas = compare_metrics(baseline_metrics, treatment_metrics)

    comparison = BenchmarkComparison(
        run_id=effective_run_id,
        generated_at=utc_now_iso(),
        baseline_results=baseline_results,
        treatment_results=treatment_results,
        baseline_metrics=baseline_metrics,
        treatment_metrics=treatment_metrics,
        delta_metrics=deltas,
    )

    comparison_json_path = run_artifact_dir / "comparison.json"
    report_path = reports_root / f"benchmark_compare_{effective_run_id}.md"
    comparison.comparison_path = write_comparison_json(comparison, comparison_json_path)
    comparison.report_path = write_markdown_report(comparison, report_path)
    return comparison

