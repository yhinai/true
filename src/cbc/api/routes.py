from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from cbc.api.store import get_benchmark, get_run, list_benchmarks, list_runs
from cbc.config import DEFAULT_CONFIG
from cbc.headless_contract import HEADLESS_CONTRACT_VERSION

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "headless_contract_version": HEADLESS_CONTRACT_VERSION}


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
