from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from cbc.review.artifacts import read_json
from cbc.review.report import compose_review_report_from_path

logger = logging.getLogger(__name__)


def _choose_artifact_root(root: Path | str) -> Path:
    resolved = Path(root).expanduser().resolve()
    return resolved


def _iter_run_files(root: Path) -> list[Path]:
    if (root / "runs").exists():
        run_root = root / "runs"
    else:
        run_root = root
    canonical = sorted(run_root.rglob("run_ledger.json"))
    if canonical:
        return canonical
    return sorted(path for path in run_root.glob("*.json") if path.is_file())


def _iter_benchmark_files(root: Path) -> list[Path]:
    if (root / "benchmarks").exists():
        bench_root = root / "benchmarks"
    else:
        bench_root = root
    canonical = sorted(bench_root.rglob("comparison.json"))
    if canonical:
        return canonical
    return sorted(path for path in bench_root.glob("*.json") if path.is_file())


def _summarize_run(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    report = compose_review_report_from_path(path)
    gate = report["summary"]["merge_gate"]["verdict"]
    verification_state = report["summary"]["verification"]["state"]
    return {
        "run_id": report["run_id"],
        "task_id": report["task_id"],
        "artifact_path": str(path),
        "merge_gate_verdict": gate,
        "verification_state": verification_state,
    }


def list_runs(artifacts_root: Path | str, limit: int = 50) -> list[dict[str, Any]]:
    root = _choose_artifact_root(artifacts_root)
    results: list[dict[str, Any]] = []

    for path in _iter_run_files(root):
        try:
            payload = read_json(path)
        except (ValueError, OSError) as exc:
            logger.warning("skipping malformed run %s: %s", path, exc)
            continue
        results.append(_summarize_run(path, payload))
        if len(results) >= limit:
            break

    results.sort(key=lambda entry: entry["run_id"])
    return results


def get_run(artifacts_root: Path | str, run_id: str) -> dict[str, Any] | None:
    root = _choose_artifact_root(artifacts_root)
    for path in _iter_run_files(root):
        try:
            payload = read_json(path)
        except (ValueError, OSError) as exc:
            logger.warning("skipping malformed run %s: %s", path, exc)
            continue
        candidate_id = str(payload.get("run_id") or payload.get("id") or "")
        if candidate_id != run_id:
            continue
        return compose_review_report_from_path(path)
    return None


def _metric(payload: dict[str, Any], *keys: str) -> Any:
    metrics = payload.get("metrics")
    if isinstance(metrics, dict):
        for key in keys:
            if key in metrics:
                return metrics[key]
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _summarize_benchmark(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    tasks = payload.get("tasks")
    total_tasks = len(tasks) if isinstance(tasks, list) else _metric(payload, "total_tasks", "task_count")
    verified_success_rate = _metric(payload, "verified_success_rate", "vsr")
    unsafe_claim_rate = _metric(payload, "unsafe_claim_rate", "ucr")
    if verified_success_rate is None and isinstance(payload.get("treatment_metrics"), dict):
        verified_success_rate = payload["treatment_metrics"].get("verified_success_rate")
    if unsafe_claim_rate is None and isinstance(payload.get("treatment_metrics"), dict):
        unsafe_claim_rate = payload["treatment_metrics"].get("unsafe_claim_rate")
    if verified_success_rate is None and isinstance(payload.get("gearbox_metrics"), dict):
        verified_success_rate = payload["gearbox_metrics"].get("verified_success_rate")
    if unsafe_claim_rate is None and isinstance(payload.get("gearbox_metrics"), dict):
        unsafe_claim_rate = payload["gearbox_metrics"].get("unsafe_claim_rate")
    if total_tasks is None and isinstance(payload.get("baseline_results"), list):
        total_tasks = len(payload["baseline_results"])
    if total_tasks is None and isinstance(payload.get("task_results"), list):
        task_ids = {
            item.get("task_id")
            for item in payload["task_results"]
            if isinstance(item, dict) and item.get("task_id")
        }
        total_tasks = len(task_ids) if task_ids else len(payload["task_results"])
    return {
        "benchmark_id": payload.get("benchmark_id") or payload.get("benchmark_name") or payload.get("run_id") or path.stem,
        "artifact_path": str(path),
        "contract": payload.get("contract"),
        "verified_success_rate": verified_success_rate,
        "unsafe_claim_rate": unsafe_claim_rate,
        "total_tasks": total_tasks,
    }


def list_benchmarks(artifacts_root: Path | str, limit: int = 50) -> list[dict[str, Any]]:
    root = _choose_artifact_root(artifacts_root)
    results: list[dict[str, Any]] = []
    for path in _iter_benchmark_files(root):
        try:
            payload = read_json(path)
        except (ValueError, OSError) as exc:
            logger.warning("skipping malformed benchmark %s: %s", path, exc)
            continue
        results.append(_summarize_benchmark(path, payload))
        if len(results) >= limit:
            break
    results.sort(key=lambda entry: str(entry["benchmark_id"]))
    return results


def get_benchmark(artifacts_root: Path | str, benchmark_id: str) -> dict[str, Any] | None:
    root = _choose_artifact_root(artifacts_root)
    for path in _iter_benchmark_files(root):
        try:
            payload = read_json(path)
        except (ValueError, OSError) as exc:
            logger.warning("skipping malformed benchmark %s: %s", path, exc)
            continue
        candidate_id = str(
            payload.get("benchmark_id")
            or payload.get("benchmark_name")
            or payload.get("run_id")
            or path.stem
        )
        if candidate_id != benchmark_id:
            continue
        payload["artifact_path"] = str(path)
        return payload
    return None
