"""Optional Supabase ledger mirror.

Zero runtime dependency: uses the Supabase PostgREST HTTP API via
``urllib`` so the existing CBC install is unaffected.

The writer is a best-effort mirror. Any failure is logged and swallowed —
the on-disk ``run_ledger.json`` remains the source of truth.

Activation: set ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` in the
environment. If either is missing, :func:`mirror_run_ledger` is a no-op.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

_RUN_FIELDS: tuple[str, ...] = (
    "run_id",
    "task_id",
    "title",
    "mode",
    "verdict",
    "adapter",
    "started_at",
    "ended_at",
)


def _creds() -> tuple[str, str] | None:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return url, key


def build_run_row(payload: dict[str, Any]) -> dict[str, Any]:
    """Project a RunLedger dict into the ``cbc_runs`` row shape."""
    row: dict[str, Any] = {key: payload.get(key) for key in _RUN_FIELDS}
    if not row.get("run_id"):
        raise ValueError("RunLedger payload missing 'run_id'")
    row["payload"] = payload
    return row


def _post(url: str, key: str, path: str, body: list[dict[str, Any]], *, upsert: bool) -> None:
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Prefer": "return=minimal,resolution=merge-duplicates" if upsert else "return=minimal",
    }
    req = urllib.request.Request(f"{url}/rest/v1/{path}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (trusted URL from env)
        resp.read()




def build_run_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Fan a RunLedger into a list of cbc_run_events rows."""
    run_id = payload.get("run_id")
    if not run_id:
        return []
    rows: list[dict[str, Any]] = []
    seq = 0
    # One "run_started" event per run
    rows.append({"run_id": run_id, "seq": seq, "kind": "run_started",
                 "payload": {"task_id": payload.get("task_id"),
                             "mode": payload.get("mode"),
                             "started_at": payload.get("started_at")}})
    seq += 1
    attempts = payload.get("attempts") or []
    for i, attempt in enumerate(attempts, start=1):
        ver = (attempt or {}).get("verification") or {}
        rows.append({"run_id": run_id, "seq": seq, "kind": "attempt_started",
                     "payload": {"attempt_index": i}})
        seq += 1
        for check in ver.get("checks") or []:
            rows.append({"run_id": run_id, "seq": seq, "kind": "check_result",
                         "payload": {"attempt_index": i,
                                     "name": check.get("name"),
                                     "status": check.get("status"),
                                     "duration_seconds": check.get("duration_seconds")}})
            seq += 1
        rows.append({"run_id": run_id, "seq": seq, "kind": "attempt_verdict",
                     "payload": {"attempt_index": i,
                                 "verdict": ver.get("verdict") or ver.get("status")}})
        seq += 1
    # Final verdict
    rows.append({"run_id": run_id, "seq": seq, "kind": "run_verdict",
                 "payload": {"verdict": payload.get("verdict"),
                             "ended_at": payload.get("ended_at")}})
    return rows


def mirror_run_ledger(payload: dict[str, Any]) -> bool:
    """Mirror a completed RunLedger to Supabase. Returns True on success.

    Best-effort: any error returns False and logs a warning.
    """
    creds = _creds()
    if creds is None:
        return False
    url, key = creds
    try:
        row = build_run_row(payload)
    except ValueError as exc:
        _LOG.warning("supabase mirror skipped: %s", exc)
        return False
    try:
        _post(url, key, "cbc_runs", [row], upsert=True)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _LOG.warning("supabase mirror failed for run %s: %s", row["run_id"], exc)
        return False
    # Fan out events (best-effort; failures don't invalidate the run mirror)
    events = build_run_events(payload)
    if events:
        try:
            _post(url, key, "cbc_run_events", events, upsert=False)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            _LOG.warning("supabase events mirror failed for run %s: %s",
                         row["run_id"], exc)
    return True


def mirror_run_ledger_path(path: str | Path) -> bool:
    """Convenience wrapper reading the ledger JSON from disk first."""
    p = Path(path)
    try:
        payload = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        _LOG.warning("supabase mirror: cannot read %s: %s", p, exc)
        return False
    return mirror_run_ledger(payload)


def mirror_run_event(
    run_id: str,
    seq: int,
    kind: str,
    payload: dict[str, Any],
) -> bool:
    """Emit a single row into ``cbc_run_events``. Best-effort."""
    creds = _creds()
    if creds is None:
        return False
    url, key = creds
    row = {"run_id": run_id, "seq": seq, "kind": kind, "payload": payload}
    try:
        _post(url, key, "cbc_run_events", [row], upsert=False)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _LOG.warning("supabase event mirror failed for run %s seq %d: %s", run_id, seq, exc)
        return False
    return True


def make_supabase_event_sink() -> Callable[[dict[str, Any]], None] | None:
    """Return a RunEventSink that mirrors events to Supabase.

    Returns ``None`` if Supabase credentials are not configured, so callers
    can compose this alongside other sinks without special-casing.
    """
    if _creds() is None:
        return None

    counters: dict[str, int] = {}

    def _sink(event: dict[str, Any]) -> None:
        run_id = event.get("run_id") or event.get("runId") or "_unknown"
        seq = counters.get(run_id, 0)
        counters[run_id] = seq + 1
        kind = str(event.get("type") or event.get("kind") or "event")
        # Strip run_id/type from the payload copy to avoid duplication.
        body = {k: v for k, v in event.items() if k not in {"run_id", "runId", "type", "kind"}}
        mirror_run_event(run_id=str(run_id), seq=seq, kind=kind, payload=body)

    return _sink
