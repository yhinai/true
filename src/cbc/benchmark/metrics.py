from __future__ import annotations

from cbc.models import BenchmarkMetrics, BenchmarkTaskResult


def compute_metrics(results: list[BenchmarkTaskResult]) -> BenchmarkMetrics:
    if not results:
        return BenchmarkMetrics(
            verified_success_rate=0.0,
            unsafe_claim_rate=0.0,
            average_retries=0.0,
            average_elapsed_seconds=0.0,
        )
    total = len(results)
    verified = sum(1 for result in results if result.verified_success)
    unsafe = sum(1 for result in results if result.unsafe_claims > 0)
    retries = sum(result.retries for result in results)
    elapsed = sum(result.elapsed_seconds for result in results)
    return BenchmarkMetrics(
        verified_success_rate=verified / total,
        unsafe_claim_rate=unsafe / total,
        average_retries=retries / total,
        average_elapsed_seconds=elapsed / total,
    )
