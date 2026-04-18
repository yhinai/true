#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _benchmark_common import REPO_ROOT
from cbc.benchmark.metrics import summarize_results
from cbc.benchmark.local_runner import load_task_paths_from_config
from cbc.benchmark.treatment import run_treatment
from cbc.config import AppConfig, PathsConfig
from cbc.intake.normalize import load_task


def build_config(artifacts_root: Path, reports_root: Path) -> AppConfig:
    return AppConfig(
        paths=PathsConfig(
            root=REPO_ROOT,
            artifacts_dir=artifacts_root,
            reports_dir=reports_root,
            prompts_dir=REPO_ROOT / "prompts",
            benchmark_config_dir=REPO_ROOT / "benchmark-configs",
            storage_db=artifacts_root / "cbc.sqlite3",
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run treatment benchmark suite.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("benchmark-configs/treatment.yaml"),
        help="Path to treatment replay-smoke config.",
    )
    parser.add_argument("--artifacts-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--reports-root", type=Path, default=Path("reports"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = (REPO_ROOT / args.config).resolve() if not args.config.is_absolute() else args.config
    artifacts_root = (REPO_ROOT / args.artifacts_root).resolve() if not args.artifacts_root.is_absolute() else args.artifacts_root
    reports_root = (REPO_ROOT / args.reports_root).resolve() if not args.reports_root.is_absolute() else args.reports_root
    app_config = build_config(artifacts_root, reports_root)

    task_paths = load_task_paths_from_config(config_path)
    results = [run_treatment(load_task(task_path), app_config) for task_path in task_paths]
    summary = summarize_results(results)
    output = {
        "suite": "treatment-smoke",
        "config_path": str(config_path),
        "summary": summary,
        "results": [
            {
                "task_id": result.task_id,
                "mode": result.mode,
                "verdict": result.verdict.value,
                "verified_success": result.verified_success,
                "unsafe_claims": result.unsafe_claims,
                "retries": result.retries,
                "elapsed_seconds": result.elapsed_seconds,
                "artifact_dir": str(result.artifact_dir),
            }
            for result in results
        ],
    }

    output_path = reports_root / "treatment-smoke" / "suite-summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"treatment run complete: {output_path}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
