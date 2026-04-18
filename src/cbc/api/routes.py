from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from cbc.api.store import get_run, list_benchmarks, list_runs
from cbc.config import DEFAULT_CONFIG
from cbc.storage.db import connect

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/runs")
def runs() -> list[dict[str, str]]:
    with connect(DEFAULT_CONFIG.paths.storage_db) as connection:
        rows = connection.execute("SELECT run_id, task_id, mode, verdict, artifact_dir, created_at FROM runs ORDER BY created_at DESC").fetchall()
    return [
        {
            "run_id": row[0],
            "task_id": row[1],
            "mode": row[2],
            "verdict": row[3],
            "artifact_dir": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


@router.get("/benchmarks")
def benchmarks() -> list[dict[str, str]]:
    with connect(DEFAULT_CONFIG.paths.storage_db) as connection:
        rows = connection.execute(
            "SELECT benchmark_id, report_dir, delta_verified_success_rate, delta_unsafe_claim_rate, created_at FROM benchmarks ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "benchmark_id": row[0],
            "report_dir": row[1],
            "delta_verified_success_rate": row[2],
            "delta_unsafe_claim_rate": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def runs_payload(root: Path, limit: int = 50) -> dict[str, list[dict[str, object]]]:
    return {"runs": list_runs(root, limit=limit)}


def run_payload(root: Path, run_id: str) -> dict[str, object] | None:
    return get_run(root, run_id)


def benchmarks_payload(root: Path, limit: int = 50) -> dict[str, list[dict[str, object]]]:
    return {"benchmarks": list_benchmarks(root, limit=limit)}
