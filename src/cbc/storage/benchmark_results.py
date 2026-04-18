from __future__ import annotations

from cbc.models import BenchmarkComparison
from cbc.storage.db import connect


def save_benchmark(db_path, comparison: BenchmarkComparison) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO benchmarks
            (benchmark_id, report_dir, delta_verified_success_rate, delta_unsafe_claim_rate, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                comparison.benchmark_id,
                str(comparison.report_dir),
                comparison.delta_verified_success_rate,
                comparison.delta_unsafe_claim_rate,
                comparison.created_at.isoformat(),
            ),
        )
