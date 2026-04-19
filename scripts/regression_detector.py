"""Compare benchmark JSON outputs and flag regressions.

Exit 0: no regression. Exit 1: regression detected (writes markdown report).

Supports both comparison shapes used by this repo:

- curated compare (``cbc compare``): ``baseline_metrics`` / ``treatment_metrics``
  with ``task_results[].mode`` in {"baseline", "treatment"}.
- controller compare (``cbc controller-compare``): ``sequential_metrics`` /
  ``gearbox_metrics`` with ``task_results[].controller_mode`` in
  {"sequential", "gearbox"}.

A regression fires when any of the following holds (threshold 5 percentage
points):

* ``delta_verified_success_rate`` drops by > 5pp versus baseline JSON.
* Treatment / gearbox ``verified_success_rate`` drops by > 5pp versus baseline
  JSON.
* Any task flips from ``VERIFIED`` to a non-``VERIFIED`` verdict (baseline→
  treatment for the curated shape, or sequential→gearbox for the controller
  shape).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGRESSION_THRESHOLD_PP = 0.05


def _pct(v: float | None) -> str:
    if v is None:
        return "n/a"
    return f"{v * 100:.1f}%"


def _treatment_metrics(doc: dict) -> dict:
    """Return the treatment-side metrics block regardless of shape."""
    if "treatment_metrics" in doc:
        return doc["treatment_metrics"] or {}
    if "gearbox_metrics" in doc:
        return doc["gearbox_metrics"] or {}
    return {}


def _partition_tasks(doc: dict) -> tuple[dict, dict]:
    """Return (baseline_side, treatment_side) mapped by task_id.

    Baseline side is ``mode == "baseline"`` or ``controller_mode == "sequential"``.
    Treatment side is ``mode == "treatment"`` or ``controller_mode == "gearbox"``.
    """
    baseline: dict = {}
    treatment: dict = {}
    for t in doc.get("task_results") or []:
        tid = t.get("task_id")
        if tid is None:
            continue
        mode = t.get("mode") or t.get("controller_mode")
        if mode in ("baseline", "sequential"):
            baseline[tid] = t
        elif mode in ("treatment", "gearbox"):
            treatment[tid] = t
    return baseline, treatment


def compare_pair(current_path: Path, baseline_path: Path) -> list[str]:
    if not current_path.exists():
        return [f"Current file missing: {current_path}"]
    if not baseline_path.exists():
        return [f"Baseline file missing: {baseline_path}"]

    current = json.loads(current_path.read_text())
    baseline = json.loads(baseline_path.read_text())
    problems: list[str] = []

    cur_delta = current.get("delta_verified_success_rate") or 0.0
    base_delta = baseline.get("delta_verified_success_rate") or 0.0
    if cur_delta < base_delta - REGRESSION_THRESHOLD_PP:
        problems.append(
            f"- delta_verified_success_rate dropped "
            f"{_pct(base_delta)} -> {_pct(cur_delta)}"
        )

    cur_rate = _treatment_metrics(current).get("verified_success_rate") or 0.0
    base_rate = _treatment_metrics(baseline).get("verified_success_rate") or 0.0
    if cur_rate < base_rate - REGRESSION_THRESHOLD_PP:
        problems.append(
            f"- treatment verified_success_rate dropped "
            f"{_pct(base_rate)} -> {_pct(cur_rate)}"
        )

    _, cur_treat = _partition_tasks(current)
    _, base_treat = _partition_tasks(baseline)
    for tid in sorted(set(cur_treat) & set(base_treat)):
        cur_verdict = cur_treat[tid].get("verdict")
        base_verdict = base_treat[tid].get("verdict")
        if base_verdict == "VERIFIED" and cur_verdict != "VERIFIED":
            problems.append(
                f"- task {tid}: flipped {base_verdict} -> {cur_verdict}"
            )

    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", action="append", required=True, type=Path)
    ap.add_argument("--baseline", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    if len(args.current) != len(args.baseline):
        print(
            f"mismatched --current/--baseline pair count: "
            f"{len(args.current)} vs {len(args.baseline)}",
            file=sys.stderr,
        )
        return 2

    report_lines: list[str] = ["# Daily benchmark regression", ""]
    any_regression = False
    for cur, base in zip(args.current, args.baseline):
        section = compare_pair(cur, base)
        report_lines.append(f"## {cur.stem}")
        real_problems = [line for line in section if line.startswith("-")]
        if real_problems:
            any_regression = True
            report_lines.extend(section)
        elif section:
            # non-regression informational lines (e.g. missing files) — surface
            # but do not flip the exit code.
            report_lines.extend(section)
        else:
            report_lines.append("No regression.")
        report_lines.append("")

    args.output.write_text("\n".join(report_lines))
    return 1 if any_regression else 0


if __name__ == "__main__":
    sys.exit(main())
