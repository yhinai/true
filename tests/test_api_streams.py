from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient

from cbc.api.app import create_app
from cbc.api.streams import _find_ledger, _sse_frame, run_stream


def _write_ledger(artifacts_root: Path, run_id: str, payload: dict) -> Path:
    run_dir = artifacts_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ledger = run_dir / "run_ledger.json"
    ledger.write_text(json.dumps(payload))
    return ledger


def test_sse_frame_shape() -> None:
    frame = _sse_frame("snapshot", {"a": 1}).decode()
    assert frame.startswith("event: snapshot\n")
    assert 'data: {"a":1}' in frame
    assert frame.endswith("\n\n")


def test_find_ledger_locates_by_run_id(tmp_path: Path) -> None:
    _write_ledger(tmp_path, "abc", {"run_id": "abc", "verdict": "VERIFIED"})
    assert _find_ledger(tmp_path, "abc") is not None
    assert _find_ledger(tmp_path, "missing") is None


def test_run_stream_emits_snapshot_and_done_on_terminal(tmp_path: Path) -> None:
    _write_ledger(tmp_path, "abc", {"run_id": "abc", "verdict": "VERIFIED"})

    async def collect() -> list[str]:
        frames: list[str] = []
        async for chunk in run_stream(tmp_path, "abc", poll_interval=0.01, max_wait=0.5):
            frames.append(chunk.decode())
            if len(frames) >= 2:
                break
        return frames

    frames = asyncio.run(collect())
    assert any(f.startswith("event: snapshot") for f in frames)
    assert any(f.startswith("event: done") for f in frames)


def test_run_stream_emits_error_when_missing(tmp_path: Path) -> None:
    async def collect() -> str:
        async for chunk in run_stream(tmp_path, "nope", poll_interval=0.01, max_wait=0.05):
            return chunk.decode()
        return ""

    frame = asyncio.run(collect())
    assert frame.startswith("event: error")


def test_http_run_stream_endpoint_returns_event_stream(tmp_path: Path, monkeypatch) -> None:
    _write_ledger(tmp_path, "abc", {"run_id": "abc", "verdict": "VERIFIED"})

    from cbc.config import DEFAULT_CONFIG

    monkeypatch.setattr(DEFAULT_CONFIG.paths, "artifacts_dir", tmp_path)

    app = create_app()
    client = TestClient(app)
    with client.stream("GET", "/runs/abc/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = b""
        for chunk in response.iter_bytes():
            body += chunk
            if b"event: done" in body:
                break
        assert b"event: snapshot" in body
        assert b"event: done" in body
