from __future__ import annotations

from pathlib import Path
from typing import Any

from .store import get_run, list_benchmarks, list_runs

try:
    from fastapi import APIRouter, HTTPException, Query
except Exception:  # pragma: no cover - exercised when fastapi is installed
    APIRouter = None  # type: ignore[assignment]
    HTTPException = RuntimeError  # type: ignore[assignment]
    Query = None  # type: ignore[assignment]


def health_payload() -> dict[str, str]:
    return {"status": "ok"}


def runs_payload(artifacts_root: Path | str, limit: int = 50) -> dict[str, Any]:
    return {"runs": list_runs(artifacts_root, limit=limit)}


def run_payload(artifacts_root: Path | str, run_id: str) -> dict[str, Any] | None:
    return get_run(artifacts_root, run_id=run_id)


def benchmarks_payload(artifacts_root: Path | str, limit: int = 50) -> dict[str, Any]:
    return {"benchmarks": list_benchmarks(artifacts_root, limit=limit)}


def build_router(artifacts_root: Path | str):
    if APIRouter is None:
        raise RuntimeError("fastapi is not installed; install fastapi to enable HTTP routes.")

    root = Path(artifacts_root)
    router = APIRouter()

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        return health_payload()

    @router.get("/runs")
    def runs(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
        return runs_payload(root, limit=limit)

    @router.get("/runs/{run_id}")
    def run_detail(run_id: str) -> dict[str, Any]:
        payload = run_payload(root, run_id=run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        return payload

    @router.get("/benchmarks")
    def benchmarks(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
        return benchmarks_payload(root, limit=limit)

    return router
