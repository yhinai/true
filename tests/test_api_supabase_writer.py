from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbc.api import supabase_writer as sw


def test_build_run_row_projects_fields() -> None:
    payload = {
        "run_id": "xyz",
        "task_id": "t1",
        "title": "demo",
        "mode": "treatment",
        "verdict": "VERIFIED",
        "adapter": "local",
        "started_at": "2026-04-19T00:00:00Z",
        "ended_at": "2026-04-19T00:00:10Z",
        "extra": "dropped-from-top-level-but-kept-in-payload",
    }
    row = sw.build_run_row(payload)
    assert row["run_id"] == "xyz"
    assert row["verdict"] == "VERIFIED"
    assert row["payload"] == payload
    assert "extra" not in row


def test_build_run_row_requires_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        sw.build_run_row({"task_id": "t"})


def test_mirror_run_ledger_noop_without_creds(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    assert sw.mirror_run_ledger({"run_id": "abc"}) is False


def test_mirror_run_ledger_calls_post_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    called = {}

    def fake_post(url, key, path, body, *, upsert):
        called.update(url=url, key=key, path=path, body=body, upsert=upsert)

    monkeypatch.setattr(sw, "_post", fake_post)
    ok = sw.mirror_run_ledger({"run_id": "abc", "verdict": "VERIFIED"})
    assert ok is True
    assert called["path"] == "cbc_runs"
    assert called["upsert"] is True
    assert called["body"][0]["run_id"] == "abc"


def test_mirror_run_ledger_path_reads_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    monkeypatch.setattr(sw, "_post", lambda *a, **k: None)
    f = tmp_path / "run_ledger.json"
    f.write_text(json.dumps({"run_id": "abc"}))
    assert sw.mirror_run_ledger_path(f) is True


def test_mirror_run_ledger_path_missing_file_returns_false(tmp_path: Path) -> None:
    assert sw.mirror_run_ledger_path(tmp_path / "nope.json") is False
