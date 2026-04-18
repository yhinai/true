from __future__ import annotations

from cbc.models import RunLedger
from cbc.storage.db import connect


def save_run(db_path, ledger: RunLedger) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO runs
            (run_id, task_id, mode, verdict, unsafe_claims, elapsed_seconds, artifact_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ledger.run_id,
                ledger.task_id,
                ledger.mode,
                ledger.verdict.value,
                ledger.unsafe_claims,
                ledger.elapsed_seconds,
                str(ledger.artifact_dir),
                ledger.started_at.isoformat(),
            ),
        )
