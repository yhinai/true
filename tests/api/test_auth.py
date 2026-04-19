from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.api.app import create_app  # noqa: E402


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(
        "cbc.api.routes.runs_payload",
        lambda root, limit=50: {"runs": []},
    )
    return TestClient(create_app())


def test_health_is_public_without_token(monkeypatch) -> None:
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    client = _client(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_is_public_even_when_token_set(monkeypatch) -> None:
    monkeypatch.setenv("CBC_API_TOKEN", "secret-token")
    client = _client(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_runs_requires_auth_when_token_set(monkeypatch) -> None:
    monkeypatch.setenv("CBC_API_TOKEN", "secret-token")
    client = _client(monkeypatch)

    unauth = client.get("/runs")
    assert unauth.status_code == 401

    bad = client.get("/runs", headers={"Authorization": "Bearer wrong"})
    assert bad.status_code == 401

    good = client.get("/runs", headers={"Authorization": "Bearer secret-token"})
    assert good.status_code == 200
    assert good.json() == {"runs": []}


def test_runs_open_when_token_unset(monkeypatch) -> None:
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    client = _client(monkeypatch)
    resp = client.get("/runs")
    assert resp.status_code == 200


def test_mirror_returns_503_when_token_unset(monkeypatch) -> None:
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    client = _client(monkeypatch)
    resp = client.post("/runs/run-123/mirror")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "auth not configured"


def test_mirror_requires_auth_when_token_set(monkeypatch) -> None:
    monkeypatch.setenv("CBC_API_TOKEN", "secret-token")
    client = _client(monkeypatch)

    unauth = client.post("/runs/run-123/mirror")
    assert unauth.status_code == 401


def test_cors_defaults_to_localhost_not_wildcard(monkeypatch) -> None:
    monkeypatch.delenv("CBC_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    client = _client(monkeypatch)

    allowed = client.options(
        "/runs",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    denied = client.options(
        "/runs",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Wildcard must NOT be the default — disallowed origins must not echo back.
    assert denied.headers.get("access-control-allow-origin") != "*"
    assert denied.headers.get("access-control-allow-origin") != "http://evil.example.com"


def test_cors_respects_env_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("CBC_CORS_ORIGINS", "https://app.example.com,https://admin.example.com")
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    client = _client(monkeypatch)

    ok = client.options(
        "/runs",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert ok.headers.get("access-control-allow-origin") == "https://app.example.com"

    nope = client.options(
        "/runs",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert nope.headers.get("access-control-allow-origin") != "*"


def test_warning_logged_when_unsafe_bind(monkeypatch, caplog) -> None:
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    with caplog.at_level(logging.WARNING, logger="cbc.api.app"):
        create_app(host="0.0.0.0")  # noqa: S104 (intentional: triggers warning)
    assert any("CBC_API_TOKEN is unset" in rec.message for rec in caplog.records)


def test_no_warning_when_localhost(monkeypatch, caplog) -> None:
    monkeypatch.delenv("CBC_API_TOKEN", raising=False)
    with caplog.at_level(logging.WARNING, logger="cbc.api.app"):
        create_app(host="127.0.0.1")
    assert not any("CBC_API_TOKEN is unset" in rec.message for rec in caplog.records)
