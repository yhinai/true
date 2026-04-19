"""Server-Sent Events helpers for the CBC API.

Two streams are exposed:

* :func:`run_stream` — tails ``run_ledger.json`` for a single run, emitting
  ``data: {json}`` frames whenever the ledger file grows or changes.
* :func:`runs_index_stream` — periodically snapshots the list of runs and
  emits a diff frame each time a new run appears or an existing verdict
  changes.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi.responses import StreamingResponse

from cbc.api.store import _iter_run_files, list_runs  # noqa: PLC2701


def simple_stream(text: str) -> StreamingResponse:
    """Legacy single-frame streamer kept for backwards compatibility."""

    async def iterator() -> AsyncIterator[bytes]:
        yield text.encode()

    return StreamingResponse(iterator(), media_type="text/plain")


def _sse_frame(event: str, payload: Any) -> bytes:
    body = json.dumps(payload, default=str, separators=(",", ":"))
    return f"event: {event}\ndata: {body}\n\n".encode()


def _find_ledger(artifacts_root: Path, run_id: str) -> Path | None:
    for path in _iter_run_files(artifacts_root):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("run_id") or data.get("id") or "") == run_id:
            return path
    return None


async def run_stream(
    artifacts_root: Path,
    run_id: str,
    *,
    poll_interval: float = 0.5,
    max_wait: float = 30.0,
) -> AsyncIterator[bytes]:
    """Tail a single run's ledger and yield SSE frames.

    Emits ``snapshot`` on first read, ``update`` on subsequent mtime
    changes, ``done`` on a terminal verdict, and ``error`` on failure.
    """
    waited = 0.0
    ledger_path: Path | None = None
    while ledger_path is None and waited < max_wait:
        ledger_path = _find_ledger(artifacts_root, run_id)
        if ledger_path is None:
            await asyncio.sleep(poll_interval)
            waited += poll_interval

    if ledger_path is None:
        yield _sse_frame("error", {"run_id": run_id, "message": "ledger not found"})
        return

    terminal = {"VERIFIED", "FALSIFIED", "TIMED_OUT", "UNPROVEN"}
    last_mtime = -1.0
    emitted_snapshot = False
    while True:
        try:
            mtime = ledger_path.stat().st_mtime
        except OSError:
            yield _sse_frame("error", {"run_id": run_id, "message": "ledger disappeared"})
            return

        if mtime != last_mtime:
            last_mtime = mtime
            try:
                payload = json.loads(ledger_path.read_text())
            except (OSError, json.JSONDecodeError):
                await asyncio.sleep(poll_interval)
                continue
            event = "snapshot" if not emitted_snapshot else "update"
            emitted_snapshot = True
            yield _sse_frame(event, payload)
            verdict = str(payload.get("verdict") or "").upper()
            if verdict in terminal:
                yield _sse_frame("done", {"run_id": run_id, "verdict": verdict})
                return

        await asyncio.sleep(poll_interval)


async def runs_index_stream(
    artifacts_root: Path,
    *,
    poll_interval: float = 1.0,
    limit: int = 50,
) -> AsyncIterator[bytes]:
    """Emit a frame each time the runs index changes."""
    last_signature: tuple[tuple[str, str], ...] | None = None
    while True:
        runs = list_runs(artifacts_root, limit=limit)
        signature = tuple(
            (str(r.get("run_id")), str(r.get("verification_state"))) for r in runs
        )
        if signature != last_signature:
            last_signature = signature
            yield _sse_frame("runs", runs)
        await asyncio.sleep(poll_interval)
