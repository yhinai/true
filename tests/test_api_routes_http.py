from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.api.app import create_app


def test_http_routes_use_payload_helpers(monkeypatch) -> None:
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr(
        "cbc.api.routes.runs_payload",
        lambda root, limit=50: {"runs": [{"run_id": "run-123", "verification_state": "VERIFIED"}]},
    )
    monkeypatch.setattr(
        "cbc.api.routes.run_payload",
        lambda root, run_id: {"run_id": run_id, "summary": {"merge_gate": {"verdict": "APPROVE"}}},
    )
    monkeypatch.setattr(
        "cbc.api.routes.benchmarks_payload",
        lambda root, limit=50: {"benchmarks": [{"benchmark_id": "bench-123"}]},
    )

    runs_response = client.get("/runs")
    assert runs_response.status_code == 200
    assert runs_response.json()["runs"][0]["run_id"] == "run-123"

    run_response = client.get("/runs/run-123")
    assert run_response.status_code == 200
    assert run_response.json()["summary"]["merge_gate"]["verdict"] == "APPROVE"

    benchmarks_response = client.get("/benchmarks")
    assert benchmarks_response.status_code == 200
    assert benchmarks_response.json()["benchmarks"][0]["benchmark_id"] == "bench-123"
