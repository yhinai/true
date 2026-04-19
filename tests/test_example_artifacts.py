from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_run_example_matches_frozen_contract() -> None:
    payload = _read_json(REPO_ROOT / "artifacts/examples/calculator_treatment/run_artifact.json")

    assert payload["contract"] == {
        "kind": "cbc.run_artifact",
        "version": "2026-04-18.v1",
    }
    assert payload["controller"]["mode"] == "gearbox"
    assert "budget_spent" in payload["controller"]
    assert "supporting_checks" in payload
    assert "policy" in payload["verification"]
    assert "/Users/alhinai/Desktop/TRUE" not in json.dumps(payload)


def test_checked_in_benchmark_examples_match_frozen_contract() -> None:
    curated = _read_json(REPO_ROOT / "reports/examples/curated_benchmark/comparison.json")
    expanded = _read_json(REPO_ROOT / "reports/examples/expanded_benchmark/comparison.json")
    controller = _read_json(REPO_ROOT / "reports/examples/controller_benchmark/comparison.json")

    assert curated["contract"] == {
        "kind": "cbc.benchmark_comparison",
        "version": "2026-04-18.v1",
    }
    assert expanded["contract"] == {
        "kind": "cbc.benchmark_comparison",
        "version": "2026-04-18.v1",
    }
    assert controller["contract"] == {
        "kind": "cbc.controller_comparison",
        "version": "2026-04-18.v1",
    }
    expanded_task_ids = {result["task_id"] for result in expanded["task_results"]}
    assert {
        "greeting_text_patch",
        "json_status_rollup",
        "shell_banner_contract",
    }.issubset(expanded_task_ids)
    assert controller["decision"]["recommended_controller"] == "sequential"


def test_checked_in_examples_do_not_contain_local_absolute_paths() -> None:
    example_paths = [
        REPO_ROOT / "artifacts/examples/calculator_treatment/run_artifact.json",
        REPO_ROOT / "artifacts/examples/slugify_property_regression_treatment/run_artifact.json",
        REPO_ROOT / "reports/examples/curated_benchmark/comparison.json",
        REPO_ROOT / "reports/examples/expanded_benchmark/comparison.json",
        REPO_ROOT / "reports/examples/controller_benchmark/comparison.json",
    ]
    for path in example_paths:
        payload = path.read_text(encoding="utf-8")
        assert "/Users/alhinai/Desktop/TRUE" not in payload
        assert "/var/folders/" not in payload
