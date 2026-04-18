from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cbc.benchmark.compare import run_comparison
from cbc.benchmark.fixtures import load_tasks_from_manifest


class BenchmarkCompareTests(unittest.TestCase):
    def test_comparison_shows_treatment_lift(self) -> None:
        manifest_path = REPO_ROOT / "fixtures/oracle_tasks/manifest.json"
        tasks = load_tasks_from_manifest(manifest_path)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            comparison = run_comparison(
                tasks=tasks,
                artifacts_root=tmp_path / "artifacts",
                reports_root=tmp_path / "reports",
                run_id="test_run_lift",
                treatment_max_retries=2,
            )

        self.assertEqual(comparison.baseline_metrics["total_tasks"], 4)
        self.assertEqual(comparison.baseline_metrics["verified_success_rate"], 0.25)
        self.assertEqual(comparison.treatment_metrics["verified_success_rate"], 1.0)
        self.assertGreater(comparison.delta_metrics["verified_success_rate_delta"], 0.0)
        self.assertLess(comparison.delta_metrics["unsafe_claim_rate_delta"], 0.0)

    def test_comparison_persists_artifacts_and_report(self) -> None:
        manifest_path = REPO_ROOT / "fixtures/oracle_tasks/manifest.json"
        tasks = load_tasks_from_manifest(manifest_path)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            comparison = run_comparison(
                tasks=tasks,
                artifacts_root=tmp_path / "artifacts",
                reports_root=tmp_path / "reports",
                run_id="test_run_artifacts",
                treatment_max_retries=2,
            )

            comparison_path = Path(comparison.comparison_path)
            report_path = Path(comparison.report_path)
            self.assertTrue(comparison_path.exists())
            self.assertTrue(report_path.exists())

            payload = json.loads(comparison_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "test_run_artifacts")
            self.assertEqual(len(payload["baseline_results"]), 4)
            self.assertEqual(len(payload["treatment_results"]), 4)

            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("| Verified Success Rate |", report_text)
            self.assertIn("| shell_exact_match |", report_text)


if __name__ == "__main__":
    unittest.main()

