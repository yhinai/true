from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.api.routes import benchmarks_payload, run_payload, runs_payload
from cbc.api.store import get_run, list_benchmarks, list_runs


class ApiStoreTests(unittest.TestCase):
    def test_list_runs_and_benchmarks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_dir = root / "runs"
            benches_dir = root / "benchmarks"
            runs_dir.mkdir(parents=True)
            benches_dir.mkdir(parents=True)

            (runs_dir / "run-a.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-a",
                        "task_id": "task-a",
                        "changed_files": [{"path": "src/cbc/api/app.py", "additions": 5, "deletions": 1}],
                        "verification": {"status": "VERIFIED", "checks": [{"name": "pytest", "status": "passed"}]},
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "run-b.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-b",
                        "task_id": "task-b",
                        "changed_files": ["src/cbc/verify/core.py"],
                        "verification": {"status": "FALSIFIED", "checks": [{"name": "oracle", "status": "failed"}]},
                    }
                ),
                encoding="utf-8",
            )
            (benches_dir / "bench-1.json").write_text(
                json.dumps(
                    {
                        "benchmark_id": "bench-1",
                        "tasks": [{"id": "task-a"}, {"id": "task-b"}],
                        "metrics": {"verified_success_rate": 0.5, "unsafe_claim_rate": 0.0},
                    }
                ),
                encoding="utf-8",
            )
            (root / "ignore.json").write_text(json.dumps({"hello": "world"}), encoding="utf-8")

            runs = list_runs(root, limit=10)
            self.assertEqual([run["run_id"] for run in runs], ["run-a", "run-b"])

            run_a = get_run(root, "run-a")
            self.assertIsNotNone(run_a)
            self.assertEqual(run_a["summary"]["merge_gate"]["verdict"], "APPROVE")

            benches = list_benchmarks(root, limit=10)
            self.assertEqual(len(benches), 1)
            self.assertEqual(benches[0]["benchmark_id"], "bench-1")
            self.assertEqual(benches[0]["total_tasks"], 2)

    def test_route_payload_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_dir = root / "runs"
            runs_dir.mkdir(parents=True)
            (runs_dir / "run-x.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-x",
                        "task_id": "task-x",
                        "verification": {"status": "UNPROVEN"},
                    }
                ),
                encoding="utf-8",
            )

            list_payload = runs_payload(root, limit=5)
            self.assertEqual(len(list_payload["runs"]), 1)
            self.assertEqual(list_payload["runs"][0]["run_id"], "run-x")

            detail_payload = run_payload(root, "run-x")
            self.assertIsNotNone(detail_payload)
            self.assertEqual(detail_payload["summary"]["verification"]["state"], "UNPROVEN")

            self.assertEqual(benchmarks_payload(root, limit=5), {"benchmarks": []})

    def test_real_comparison_shape_is_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benches_dir = root / "benchmarks"
            benches_dir.mkdir(parents=True)
            (benches_dir / "comparison.json").write_text(
                json.dumps(
                    {
                        "benchmark_id": "cmp-1",
                        "task_results": [
                            {"task_id": "task-a", "mode": "baseline"},
                            {"task_id": "task-b", "mode": "baseline"},
                            {"task_id": "task-a", "mode": "treatment"},
                            {"task_id": "task-b", "mode": "treatment"},
                        ],
                        "treatment_metrics": {
                            "verified_success_rate": 1.0,
                            "unsafe_claim_rate": 0.0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            benches = list_benchmarks(root, limit=10)
            self.assertEqual(len(benches), 1)
            self.assertEqual(benches[0]["benchmark_id"], "cmp-1")
            self.assertEqual(benches[0]["total_tasks"], 2)
            self.assertEqual(benches[0]["verified_success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
