from __future__ import annotations

import json
import logging
from pathlib import Path

from cbc.api.store import get_benchmark, get_run, list_benchmarks, list_runs


def _write_good_run(runs_dir: Path, run_id: str) -> None:
    (runs_dir / f"{run_id}.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": f"task-{run_id}",
                "changed_files": [],
                "verification": {
                    "status": "VERIFIED",
                    "checks": [{"name": "oracle", "status": "passed"}],
                },
            }
        ),
        encoding="utf-8",
    )


def test_list_runs_skips_malformed_and_logs_warning(tmp_path: Path, caplog) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)
    _write_good_run(runs_dir, "run-good")
    (runs_dir / "run-bad.json").write_text("{not valid json", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="cbc.api.store"):
        runs = list_runs(tmp_path, limit=10)

    assert [r["run_id"] for r in runs] == ["run-good"]
    assert any("skipping malformed run" in rec.message for rec in caplog.records)


def test_get_run_skips_malformed_and_logs_warning(tmp_path: Path, caplog) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "broken.json").write_text("not-json-at-all", encoding="utf-8")
    _write_good_run(runs_dir, "run-target")

    with caplog.at_level(logging.WARNING, logger="cbc.api.store"):
        result = get_run(tmp_path, "run-target")

    assert result is not None
    assert result["run_id"] == "run-target"
    assert any("skipping malformed run" in rec.message for rec in caplog.records)


def test_list_benchmarks_skips_malformed_and_logs_warning(tmp_path: Path, caplog) -> None:
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir(parents=True)
    (bench_dir / "good.json").write_text(
        json.dumps({"benchmark_id": "b-ok", "tasks": []}),
        encoding="utf-8",
    )
    (bench_dir / "bad.json").write_text("###garbage###", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="cbc.api.store"):
        benches = list_benchmarks(tmp_path, limit=10)

    assert [b["benchmark_id"] for b in benches] == ["b-ok"]
    assert any("skipping malformed benchmark" in rec.message for rec in caplog.records)


def test_get_benchmark_skips_malformed_and_logs_warning(tmp_path: Path, caplog) -> None:
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir(parents=True)
    (bench_dir / "bad.json").write_text("not json", encoding="utf-8")
    (bench_dir / "good.json").write_text(
        json.dumps({"benchmark_id": "b-target", "tasks": []}),
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING, logger="cbc.api.store"):
        result = get_benchmark(tmp_path, "b-target")

    assert result is not None
    assert result["benchmark_id"] == "b-target"
    assert any("skipping malformed benchmark" in rec.message for rec in caplog.records)
