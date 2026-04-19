from __future__ import annotations

from cbc.models import RunLedger
from cbc.storage.db import connect


def save_run(db_path, ledger: RunLedger) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO runs
            (run_id, task_id, mode, verdict, unsafe_claims, elapsed_seconds, total_tokens, estimated_cost_usd, artifact_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ledger.run_id,
                ledger.task_id,
                ledger.mode,
                ledger.verdict.value,
                ledger.unsafe_claims,
                ledger.elapsed_seconds,
                ledger.total_tokens,
                ledger.estimated_cost_usd,
                str(ledger.artifact_dir),
                ledger.started_at.isoformat(),
            ),
        )


def load_recent_runs(db_path, *, limit: int = 20) -> list[dict[str, object]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT run_id, task_id, mode, verdict, unsafe_claims, elapsed_seconds, total_tokens, estimated_cost_usd, artifact_dir, created_at
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "run_id": row[0],
            "task_id": row[1],
            "mode": row[2],
            "verdict": row[3],
            "unsafe_claims": row[4],
            "elapsed_seconds": row[5],
            "total_tokens": row[6],
            "estimated_cost_usd": row[7],
            "artifact_dir": row[8],
            "created_at": row[9],
        }
        for row in rows
    ]
