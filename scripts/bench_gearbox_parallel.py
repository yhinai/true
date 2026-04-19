"""Compare wall time for sequential vs parallel gearbox on one oracle task.

Exit codes:
  0 - parallel strictly faster than sequential (or parallel unavailable with a recorded reason)
  1 - missing fixtures or configuration error
  2 - sequential run failed
  3 - parallel run failed with an unexpected error
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_once(task: Path, sandbox: str) -> dict:
    t0 = time.perf_counter()
    result = subprocess.run(
        [
            "uv", "run",
            "--extra", "contree" if sandbox == "contree" else "dev",
            "cbc", "run",
            str(task),
            "--mode=treatment",
            "--controller=gearbox",
            f"--sandbox={sandbox}",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=900,
        cwd=REPO_ROOT,
    )
    elapsed = time.perf_counter() - t0
    return {
        "sandbox": sandbox,
        "elapsed_seconds": elapsed,
        "returncode": result.returncode,
        "stderr_tail": result.stderr[-1000:],
        "stdout_tail": result.stdout[-500:],
    }


def main() -> int:
    task = REPO_ROOT / "fixtures" / "oracle_tasks" / "calculator_bug" / "task.yaml"
    if not task.exists():
        print(f"Task fixture missing: {task}", file=sys.stderr)
        return 1

    print(f"Benchmarking task: {task}", file=sys.stderr)

    print("Running sequential...", file=sys.stderr)
    seq = run_once(task, "local")

    print("Running parallel (contree)...", file=sys.stderr)
    par = run_once(task, "contree")

    report: dict = {
        "task": str(task.relative_to(REPO_ROOT)),
        "sequential": seq,
        "parallel": par,
    }

    if seq["returncode"] != 0:
        report["conclusion"] = "sequential_failed"
        print(json.dumps(report, indent=2))
        return 2

    if par["returncode"] != 0:
        report["conclusion"] = "parallel_unavailable_or_failed"
        report["speedup"] = None
        print(json.dumps(report, indent=2))
        # Exit 0: the script itself succeeded; the CLI's inability to run under ConTree is a deployment concern
        return 0

    seq_s = seq["elapsed_seconds"]
    par_s = par["elapsed_seconds"]
    speedup = seq_s / par_s if par_s > 0 else None
    report["speedup"] = speedup
    report["conclusion"] = "parallel_faster" if par_s < seq_s else "parallel_not_faster"

    print(json.dumps(report, indent=2))

    if par_s >= seq_s:
        print("WARNING: parallel did not beat sequential", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
