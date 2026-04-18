from __future__ import annotations

from statistics import fmean, median

from .types import BenchmarkTaskResult


def summarize_results(results: list[BenchmarkTaskResult]) -> dict[str, float | int]:
    if not results:
        return {
            "total_tasks": 0,
            "verified_tasks": 0,
            "verified_success_rate": 0.0,
            "unsafe_claim_tasks": 0,
            "unsafe_claim_rate": 0.0,
            "mean_attempt_count": 0.0,
            "mean_retries": 0.0,
            "mean_duration_s": 0.0,
            "median_duration_s": 0.0,
        }

    total = len(results)
    verified = sum(1 for result in results if result.verified)
    unsafe = sum(1 for result in results if result.unsafe_claim)
    attempts = [result.attempt_count for result in results]
    retries = [result.retries_used for result in results]
    durations = [result.duration_s for result in results]

    return {
        "total_tasks": total,
        "verified_tasks": verified,
        "verified_success_rate": round(verified / total, 4),
        "unsafe_claim_tasks": unsafe,
        "unsafe_claim_rate": round(unsafe / total, 4),
        "mean_attempt_count": round(fmean(attempts), 4),
        "mean_retries": round(fmean(retries), 4),
        "mean_duration_s": round(fmean(durations), 4),
        "median_duration_s": round(float(median(durations)), 4),
    }


def compare_metrics(
    baseline_metrics: dict[str, float | int], treatment_metrics: dict[str, float | int]
) -> dict[str, float]:
    verified_delta = float(treatment_metrics["verified_success_rate"]) - float(
        baseline_metrics["verified_success_rate"]
    )
    unsafe_delta = float(treatment_metrics["unsafe_claim_rate"]) - float(
        baseline_metrics["unsafe_claim_rate"]
    )
    latency_delta = float(treatment_metrics["mean_duration_s"]) - float(
        baseline_metrics["mean_duration_s"]
    )
    retries_delta = float(treatment_metrics["mean_retries"]) - float(
        baseline_metrics["mean_retries"]
    )
    return {
        "verified_success_rate_delta": round(verified_delta, 4),
        "unsafe_claim_rate_delta": round(unsafe_delta, 4),
        "mean_duration_s_delta": round(latency_delta, 4),
        "mean_retries_delta": round(retries_delta, 4),
    }

