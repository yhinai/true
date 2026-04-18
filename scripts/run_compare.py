#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _benchmark_common import REPO_ROOT, load_json
from cbc.benchmark.compare import run_comparison
from cbc.benchmark.fixtures import load_tasks_from_manifest
from cbc.benchmark.types import to_builtin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline vs treatment comparison.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("benchmark-configs/compare.json"),
        help="Path to benchmark comparison JSON config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = (REPO_ROOT / args.config).resolve() if not args.config.is_absolute() else args.config
    config = load_json(config_path)

    manifest_path = (REPO_ROOT / config["manifest_path"]).resolve()
    task_ids: list[str] | None = None
    subset_path_raw = config.get("subset_path")
    if subset_path_raw:
        subset_path = (REPO_ROOT / subset_path_raw).resolve()
        subset_config = load_json(subset_path)
        task_ids = list(subset_config.get("task_ids", []))
    elif config.get("task_ids"):
        task_ids = list(config["task_ids"])

    tasks = load_tasks_from_manifest(manifest_path, include_task_ids=task_ids)
    comparison = run_comparison(
        tasks=tasks,
        baseline_timeout_s=int(config.get("baseline_timeout_s", 30)),
        treatment_timeout_s=int(config.get("treatment_timeout_s", 30)),
        treatment_max_retries=int(config.get("treatment_max_retries", 2)),
        artifacts_root=(REPO_ROOT / config.get("artifacts_root", "artifacts")).resolve(),
        reports_root=(REPO_ROOT / config.get("reports_root", "reports")).resolve(),
    )

    print(f"comparison json: {comparison.comparison_path}")
    print(f"comparison report: {comparison.report_path}")
    print(json.dumps(to_builtin(comparison.delta_metrics), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

