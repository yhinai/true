from __future__ import annotations

from pathlib import Path
from typing import Any

from cbc.review.artifacts import iter_json_files, read_json
from cbc.review.report import compose_review_report


def _looks_like_run(payload: dict[str, Any]) -> bool:
    has_identity = any(key in payload for key in ("run_id", "id"))
    has_verification = any(key in payload for key in ("verification", "verification_report"))
    return has_identity and has_verification


def _looks_like_benchmark(payload: dict[str, Any]) -> bool:
    return any(
        key in payload
        for key in (
            "benchmark_id",
            "benchmark_name",
            "tasks",
            "comparison",
            "metrics",
            "baseline_metrics",
            "treatment_metrics",
            "delta_metrics",
        )
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
    verified_success_rate = _metric(payload, "verified_success_rate", "vsr")
    unsafe_claim_rate = _metric(payload, "unsafe_claim_rate", "ucr")
    if verified_success_rate is None and isinstance(payload.get("treatment_metrics"), dict):
        verified_success_rate = payload["treatment_metrics"].get("verified_success_rate")
    if unsafe_claim_rate is None and isinstance(payload.get("treatment_metrics"), dict):
        unsafe_claim_rate = payload["treatment_metrics"].get("unsafe_claim_rate")
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
        "verified_success_rate": verified_success_rate,
        "unsafe_claim_rate": unsafe_claim_rate,
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
