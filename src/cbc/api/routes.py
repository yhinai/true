from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from cbc.api.store import get_benchmark, get_run, list_benchmarks, list_runs
from cbc.api.streams import _find_ledger, run_stream, runs_index_stream
from cbc.api.supabase_writer import mirror_run_ledger_path
from cbc.config import DEFAULT_CONFIG
from cbc.headless_contract import HEADLESS_CONTRACT_VERSION

router = APIRouter()

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "headless_contract_version": HEADLESS_CONTRACT_VERSION}


@router.get("/runs/{run_id}/stream")
def run_detail_stream(run_id: str) -> StreamingResponse:
    return StreamingResponse(
        run_stream(DEFAULT_CONFIG.paths.artifacts_dir, run_id),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/runs.stream")
def runs_index_sse() -> StreamingResponse:
    return StreamingResponse(
        runs_index_stream(DEFAULT_CONFIG.paths.artifacts_dir),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/runs/{run_id}/mirror")
def mirror_run(run_id: str) -> dict[str, object]:
    """Force-mirror a completed run to Supabase (if configured)."""
    ledger = _find_ledger(DEFAULT_CONFIG.paths.artifacts_dir, run_id)
    if ledger is None:
        raise HTTPException(status_code=404, detail="run not found")
    ok = mirror_run_ledger_path(ledger)
    return {"run_id": run_id, "mirrored": ok}


@router.get("/runs")
def runs() -> dict[str, list[dict[str, object]]]:
    return runs_payload(DEFAULT_CONFIG.paths.artifacts_dir)


@router.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, object] | None:
    return run_payload(DEFAULT_CONFIG.paths.artifacts_dir, run_id)


@router.get("/benchmarks")
def benchmarks() -> dict[str, list[dict[str, object]]]:
    return benchmarks_payload(DEFAULT_CONFIG.paths.reports_dir)


@router.get("/benchmarks/{benchmark_id}")
def benchmark_detail(benchmark_id: str) -> dict[str, object] | None:
    return benchmark_payload(DEFAULT_CONFIG.paths.reports_dir, benchmark_id)


def runs_payload(root: Path, limit: int = 50) -> dict[str, list[dict[str, object]]]:
    return {"runs": list_runs(root, limit=limit)}


def run_payload(root: Path, run_id: str) -> dict[str, object] | None:
    return get_run(root, run_id)


def benchmarks_payload(root: Path, limit: int = 50) -> dict[str, list[dict[str, object]]]:
    return {"benchmarks": list_benchmarks(root, limit=limit)}


def benchmark_payload(root: Path, benchmark_id: str) -> dict[str, object] | None:
    return get_benchmark(root, benchmark_id)
