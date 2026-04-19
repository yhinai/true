from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from cbc.benchmark.reports import save_controller_benchmark_report
from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.controller.orchestrator import run_task
from cbc.intake.normalize import load_task
from cbc.models import (
    ControllerBenchmarkComparison,
    ControllerBenchmarkMetrics,
    ControllerBenchmarkTaskResult,
    ControllerDecision,
)
from cbc.storage.artifacts import create_artifact_dir


def run_controller_comparison(
    *,
    task_paths: list[Path],
    config_path: Path,
    config: AppConfig = DEFAULT_CONFIG,
) -> ControllerBenchmarkComparison:
    sequential_results: list[ControllerBenchmarkTaskResult] = []
    gearbox_results: list[ControllerBenchmarkTaskResult] = []
    for task_path in task_paths:
        task = load_task(task_path)
        sequential_results.append(_run_controller_arm(task, controller_mode="sequential", config=config))
        gearbox_results.append(_run_controller_arm(task, controller_mode="gearbox", config=config))

    sequential_metrics = _compute_controller_metrics(sequential_results)
    gearbox_metrics = _compute_controller_metrics(gearbox_results)
    decision = _decide_default(sequential_metrics, gearbox_metrics)
    report_dir = create_artifact_dir(config.paths.reports_dir, "benchmarks")
    comparison = ControllerBenchmarkComparison(
        benchmark_id=uuid4().hex[:12],
        config_path=config_path,
        task_results=sequential_results + gearbox_results,
        sequential_metrics=sequential_metrics,
        gearbox_metrics=gearbox_metrics,
        delta_verified_success_rate=gearbox_metrics.verified_success_rate - sequential_metrics.verified_success_rate,
        delta_unsafe_claim_rate=sequential_metrics.unsafe_claim_rate - gearbox_metrics.unsafe_claim_rate,
        delta_average_retries=gearbox_metrics.average_retries - sequential_metrics.average_retries,
        delta_average_elapsed_seconds=gearbox_metrics.average_elapsed_seconds - sequential_metrics.average_elapsed_seconds,
        delta_average_model_calls=gearbox_metrics.average_model_calls - sequential_metrics.average_model_calls,
        decision=decision,
        report_dir=report_dir,
    )
    save_controller_benchmark_report(comparison)
    return comparison


def _run_controller_arm(task, *, controller_mode: str, config: AppConfig) -> ControllerBenchmarkTaskResult:
    ledger = run_task(task, mode="treatment", config=config, controller_mode=controller_mode)
    return ControllerBenchmarkTaskResult(
        task_id=task.task_id,
        controller_mode=controller_mode,
        verdict=ledger.verdict,
        verified_success=ledger.verdict.value == "VERIFIED",
        unsafe_claims=ledger.unsafe_claims,
        retries=max(len(ledger.attempts) - 1, 0),
        elapsed_seconds=ledger.elapsed_seconds,
        model_calls_used=ledger.model_calls_used,
        candidate_evaluations=len(ledger.candidate_results),
        total_tokens=ledger.total_tokens,
        estimated_cost_usd=ledger.estimated_cost_usd,
        selected_candidate_id=ledger.selected_candidate_id,
        artifact_dir=ledger.artifact_dir,
    )


def _compute_controller_metrics(results: list[ControllerBenchmarkTaskResult]) -> ControllerBenchmarkMetrics:
    if not results:
        return ControllerBenchmarkMetrics(
            verified_success_rate=0.0,
            unsafe_claim_rate=0.0,
            average_retries=0.0,
            average_elapsed_seconds=0.0,
            average_model_calls=0.0,
            average_candidate_evaluations=0.0,
            average_total_tokens=0.0,
            average_estimated_cost_usd=0.0,
        )
    total = len(results)
    verified = sum(1 for result in results if result.verified_success)
    unsafe = sum(1 for result in results if result.unsafe_claims > 0)
    retries = sum(result.retries for result in results)
    elapsed = sum(result.elapsed_seconds for result in results)
    model_calls = sum(result.model_calls_used for result in results)
    candidate_evaluations = sum(result.candidate_evaluations for result in results)
    total_tokens = sum(result.total_tokens for result in results)
    total_cost = sum(result.estimated_cost_usd or 0.0 for result in results)
    return ControllerBenchmarkMetrics(
        verified_success_rate=verified / total,
        unsafe_claim_rate=unsafe / total,
        average_retries=retries / total,
        average_elapsed_seconds=elapsed / total,
        average_model_calls=model_calls / total,
        average_candidate_evaluations=candidate_evaluations / total,
        average_total_tokens=total_tokens / total,
        average_estimated_cost_usd=total_cost / total,
    )


def _decide_default(
    sequential: ControllerBenchmarkMetrics,
    gearbox: ControllerBenchmarkMetrics,
) -> ControllerDecision:
    if (
        gearbox.verified_success_rate > sequential.verified_success_rate
        and gearbox.unsafe_claim_rate <= sequential.unsafe_claim_rate
    ):
        return ControllerDecision(
            recommended_controller="gearbox",
            should_promote_to_default=True,
            rationale=(
                "Gearbox improved verified success rate without worsening unsafe claims "
                "on the checked-in controller benchmark subset."
            ),
        )

    reasons: list[str] = []
    if gearbox.verified_success_rate <= sequential.verified_success_rate:
        reasons.append("no verified-success lift")
    if gearbox.unsafe_claim_rate > sequential.unsafe_claim_rate:
        reasons.append("unsafe-claim rate worsened")
    if gearbox.average_model_calls > sequential.average_model_calls:
        reasons.append("gearbox spends more model calls")
    if not reasons:
        reasons.append("sequential remains the simpler truthful default")
    return ControllerDecision(
        recommended_controller="sequential",
        should_promote_to_default=False,
        rationale=(
            "Keep gearbox opt-in for now because "
            + ", ".join(reasons)
            + " on the checked-in controller benchmark subset."
        ),
    )
