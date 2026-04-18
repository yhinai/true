#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _benchmark_common import REPO_ROOT, load_json
from cbc.benchmark.baseline import run_baseline_suite
from cbc.benchmark.fixtures import load_tasks_from_manifest
from cbc.benchmark.metrics import summarize_results
from cbc.benchmark.types import to_builtin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline benchmark suite.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("benchmark-configs/baseline.json"),
        help="Path to baseline JSON config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = (REPO_ROOT / args.config).resolve() if not args.config.is_absolute() else args.config
    config = load_json(config_path)

    manifest_path = (REPO_ROOT / config["manifest_path"]).resolve()
    task_ids = config.get("task_ids") or None
    timeout_s = int(config.get("timeout_s", 30))
    artifacts_root = (REPO_ROOT / config.get("artifacts_root", "artifacts")).resolve()

    tasks = load_tasks_from_manifest(manifest_path, include_task_ids=task_ids)
    run_dir = artifacts_root / "benchmark" / "baseline_latest"
    results = run_baseline_suite(tasks, timeout_s=timeout_s, artifact_dir=run_dir)
    summary = summarize_results(results)
    output = {"summary": summary, "results": to_builtin(results)}

    output_path = run_dir / "baseline_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"baseline run complete: {output_path}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

