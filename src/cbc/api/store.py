from __future__ import annotations

from pathlib import Path
from typing import Any

from cbc.review.artifacts import iter_json_files, read_json
from cbc.review.report import compose_review_report


def _looks_like_run(payload: dict[str, Any]) -> bool:
    return any(
        key in payload
        for key in ("run_id", "verification", "verification_report", "diff", "changed_files", "task_id")
    )


def _looks_like_benchmark(payload: dict[str, Any]) -> bool:
    return any(
        key in payload for key in ("benchmark_id", "benchmark_name", "tasks", "comparison", "metrics")
    )


def _choose_artifact_root(root: Path | str) -> Path:
    resolved = Path(root).expanduser().resolve()
    return resolved


def _summarize_run(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    report = compose_review_report(payload)
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

    for path in iter_json_files(root):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if not _looks_like_run(payload):
            continue
        results.append(_summarize_run(path, payload))
        if len(results) >= limit:
            break

    results.sort(key=lambda entry: entry["run_id"])
    return results


def get_run(artifacts_root: Path | str, run_id: str) -> dict[str, Any] | None:
    root = _choose_artifact_root(artifacts_root)
    for path in iter_json_files(root):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if not _looks_like_run(payload):
            continue
        candidate_id = str(payload.get("run_id") or payload.get("id") or "")
        if candidate_id != run_id:
            continue
        report = compose_review_report(payload)
        report["artifact_path"] = str(path)
        return report
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
    return {
        "benchmark_id": payload.get("benchmark_id") or payload.get("benchmark_name") or path.stem,
        "artifact_path": str(path),
        "verified_success_rate": _metric(payload, "verified_success_rate", "vsr"),
        "unsafe_claim_rate": _metric(payload, "unsafe_claim_rate", "ucr"),
        "total_tasks": total_tasks,
    }


def list_benchmarks(artifacts_root: Path | str, limit: int = 50) -> list[dict[str, Any]]:
    root = _choose_artifact_root(artifacts_root)
    results: list[dict[str, Any]] = []
    for path in iter_json_files(root):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if not _looks_like_benchmark(payload):
            continue
        results.append(_summarize_benchmark(path, payload))
        if len(results) >= limit:
            break
    results.sort(key=lambda entry: str(entry["benchmark_id"]))
    return results
