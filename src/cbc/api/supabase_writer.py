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
