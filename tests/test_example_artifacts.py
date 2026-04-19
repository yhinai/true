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


def test_checked_in_benchmark_examples_match_frozen_contract() -> None:
    curated = _read_json(REPO_ROOT / "reports/examples/curated_benchmark/comparison.json")
    controller = _read_json(REPO_ROOT / "reports/examples/controller_benchmark/comparison.json")

    assert curated["contract"] == {
        "kind": "cbc.benchmark_comparison",
        "version": "2026-04-18.v1",
    }
    assert controller["contract"] == {
        "kind": "cbc.controller_comparison",
        "version": "2026-04-18.v1",
    }
    assert controller["decision"]["recommended_controller"] == "sequential"
