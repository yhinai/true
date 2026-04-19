from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.review.report import compose_review_report


class ReviewReportTests(unittest.TestCase):
    def test_verified_run_yields_approve(self) -> None:
        run_artifact = {
            "run_id": "run-001",
            "task_id": "task-alpha",
            "diff": {
                "files": [
                    {"path": "src/cbc/review/report.py", "additions": 20, "deletions": 3, "status": "modified"}
                ]
            },
            "verification": {
                "status": "VERIFIED",
                "checks": [{"name": "pytest", "status": "passed"}],
            },
        }

        report = compose_review_report(run_artifact)
        self.assertEqual(report["contract"]["kind"], "cbc.review_report")
        self.assertEqual(report["run_id"], "run-001")
        self.assertEqual(report["summary"]["merge_gate"]["verdict"], "APPROVE")
        self.assertEqual(report["summary"]["risk"]["risk_level"], "LOW")

    def test_unsafe_claim_yields_unsafe(self) -> None:
        run_artifact = {
            "run_id": "run-unsafe",
            "changed_files": ["src/cbc/verify/core.py"],
            "verification": {"status": "FALSIFIED", "checks": [{"name": "oracle", "status": "failed"}]},
            "unsafe_claim": True,
        }

        report = compose_review_report(run_artifact)
        self.assertEqual(report["summary"]["merge_gate"]["verdict"], "UNSAFE")
        self.assertEqual(report["summary"]["risk"]["risk_level"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
