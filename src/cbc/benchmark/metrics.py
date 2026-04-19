from __future__ import annotations

from cbc.models import BenchmarkMetrics, BenchmarkTaskResult


def compute_metrics(results: list[BenchmarkTaskResult]) -> BenchmarkMetrics:
    if not results:
        return BenchmarkMetrics(
            verified_success_rate=0.0,
            unsafe_claim_rate=0.0,
            average_retries=0.0,
            average_elapsed_seconds=0.0,
            average_total_tokens=0.0,
            average_estimated_cost_usd=0.0,
        )
    total = len(results)
    verified = sum(1 for result in results if result.verified_success)
    unsafe = sum(1 for result in results if result.unsafe_claims > 0)
    retries = sum(result.retries for result in results)
    elapsed = sum(result.elapsed_seconds for result in results)
    total_tokens = sum(result.total_tokens for result in results)
    total_cost = sum(result.estimated_cost_usd or 0.0 for result in results)
    return BenchmarkMetrics(
        verified_success_rate=verified / total,
        unsafe_claim_rate=unsafe / total,
        average_retries=retries / total,
        average_elapsed_seconds=elapsed / total,
        average_total_tokens=total_tokens / total,
        average_estimated_cost_usd=total_cost / total,
    )


def summarize_results(results: list[object]) -> dict[str, float]:
    if not results:
        return {
            "task_count": 0,
            "verified_success_rate": 0.0,
            "unsafe_claim_rate": 0.0,
            "average_attempt_count": 0.0,
            "average_retries": 0.0,
            "average_duration_s": 0.0,
        }

    task_count = len(results)
    verified = 0
    unsafe = 0
    attempts = 0
    retries = 0
    duration = 0.0
    for result in results:
        verified += int(bool(getattr(result, "verified", getattr(result, "verified_success", False))))
        unsafe += int(bool(getattr(result, "unsafe_claim", False) or getattr(result, "unsafe_claims", 0)))
        attempts += int(getattr(result, "attempt_count", getattr(result, "retries", 0) + 1))
        retries += int(getattr(result, "retries_used", getattr(result, "retries", 0)))
        duration += float(getattr(result, "duration_s", getattr(result, "elapsed_seconds", 0.0)))

    return {
        "task_count": task_count,
        "verified_success_rate": verified / task_count,
        "unsafe_claim_rate": unsafe / task_count,
        "average_attempt_count": attempts / task_count,
        "average_retries": retries / task_count,
        "average_duration_s": duration / task_count,
    }
