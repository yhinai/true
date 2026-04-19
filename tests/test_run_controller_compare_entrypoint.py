from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_run_controller_compare_direct_invocation_bootstraps_with_uv(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.yaml"
    config_path.write_text(
        "tasks:\n"
        f"  - {(REPO_ROOT / 'fixtures/oracle_tasks/title_case_bug/task.yaml').resolve()}\n"
        "controller:\n"
        "  budget:\n"
        "    max_model_calls_per_run: 4\n",
        encoding="utf-8",
    )
    artifacts_root = tmp_path / "artifacts"
    reports_root = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "scripts/run_controller_compare.py",
            "--config",
            str(config_path),
            "--artifacts-root",
            str(artifacts_root),
            "--reports-root",
            str(reports_root),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "re-running with `uv run`" in result.stderr
    assert "comparison json:" in result.stdout

    compare_json = reports_root / "controller-compare" / "compare.json"
    compare_markdown = reports_root / "controller-compare" / "compare.md"
    assert compare_json.exists()
    assert compare_markdown.exists()

    payload = json.loads(compare_json.read_text(encoding="utf-8"))
    assert payload["config_path"] == str(config_path.resolve())
    assert payload["decision"]["recommended_controller"] == "sequential"
