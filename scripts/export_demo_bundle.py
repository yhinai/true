#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from _benchmark_common import REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export latest benchmark comparison artifacts.")
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=Path("artifacts/benchmark"),
        help="Root containing benchmark run directories.",
    )
    parser.add_argument(
        "--reports-root",
        type=Path,
        default=Path("reports"),
        help="Root containing benchmark markdown reports.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/demo_bundle"),
        help="Output directory for copied demo artifacts.",
    )
    return parser.parse_args()


def _latest_run_dir(root: Path) -> Path:
    run_dirs = [entry for entry in root.glob("*") if entry.is_dir()]
    if not run_dirs:
        msg = f"No benchmark run directories found under {root}"
        raise FileNotFoundError(msg)
    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def main() -> int:
    args = parse_args()
    artifacts_root = (REPO_ROOT / args.artifacts_root).resolve()
    reports_root = (REPO_ROOT / args.reports_root).resolve()
    output_dir = (REPO_ROOT / args.out).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    latest_run = _latest_run_dir(artifacts_root)
    comparison_json = latest_run / "comparison.json"
    if not comparison_json.exists():
        msg = f"comparison.json missing in latest run directory: {latest_run}"
        raise FileNotFoundError(msg)

    report_candidates = sorted(reports_root.glob("benchmark_compare_*.md"), key=lambda p: p.stat().st_mtime)
    if not report_candidates:
        msg = f"No comparison reports found under {reports_root}"
        raise FileNotFoundError(msg)
    latest_report = report_candidates[-1]

    copied_json = output_dir / comparison_json.name
    copied_report = output_dir / latest_report.name
    shutil.copy2(comparison_json, copied_json)
    shutil.copy2(latest_report, copied_report)

    manifest = {
        "latest_run_dir": str(latest_run),
        "comparison_json": str(copied_json),
        "comparison_report": str(copied_report),
    }
    manifest_path = output_dir / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"demo bundle exported: {output_dir}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

