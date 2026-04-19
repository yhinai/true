#!/usr/bin/env python3
"""Pipe `cbc run --stream` JSONL into Supabase realtime in real time.

Usage:
    cbc run <task> --stream | python3 scripts/stream_to_supabase.py <task.yaml>

Env required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY (preferred) or NEXT_PUBLIC_SUPABASE_ANON_KEY

Flow:
1. On the first event carrying a run_id, upsert a cbc_runs row with
   verdict='PENDING' so subsequent events satisfy the FK.
2. For each event, POST to cbc_run_events.
3. On run.completed, PATCH the cbc_runs row with the final verdict/tokens.

stdout is pass-through so CI still captures the raw event log.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
)


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    h = {
        "apikey": KEY or "",
        "Authorization": f"Bearer {KEY or ''}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _request(method: str, path: str, body: dict | None, extra: dict | None = None) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers=_headers(extra),
        method=method,
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(
            f"[mirror] {method} {path} http={exc.code} body={exc.read()[:220]!r}\n"
        )
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[mirror] {method} {path} error: {exc}\n")


def upsert_run(row: dict) -> None:
    _request(
        "POST",
        "cbc_runs",
        row,
        extra={"Prefer": "resolution=merge-duplicates,return=minimal"},
    )


def insert_event(row: dict) -> None:
    _request(
        "POST",
        "cbc_run_events",
        row,
        extra={"Prefer": "return=minimal"},
    )


def patch_run(run_id: str, patch: dict) -> None:
    q = urllib.parse.urlencode({"run_id": f"eq.{run_id}"})
    _request(
        "PATCH",
        f"cbc_runs?{q}",
        patch,
        extra={"Prefer": "return=minimal"},
    )


def load_task_meta(task_path: str | None) -> dict[str, str | None]:
    meta: dict[str, str | None] = {"task_id": None, "title": None}
    if not task_path:
        return meta
    p = Path(task_path)
    if not p.exists():
        return meta
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return meta
    # Minimal YAML peek without pulling PyYAML; the task files have "id: foo"
    # and "title: bar" on their own lines near the top.
    for line in text.splitlines()[:20]:
        stripped = line.strip()
        if (stripped.startswith("task_id:") or stripped.startswith("id:")) and meta["task_id"] is None:
            meta["task_id"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("title:") and meta["title"] is None:
            meta["title"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return meta


def passthrough_only(msg: str) -> None:
    sys.stderr.write(f"[mirror] {msg} — streaming without mirror.\n")
    for line in sys.stdin:
        sys.stdout.write(line)
        sys.stdout.flush()


def main(argv: list[str]) -> int:
    task_path = argv[1] if len(argv) > 1 else os.environ.get("TASK")
    if not SUPABASE_URL or not KEY:
        passthrough_only("SUPABASE_URL or key missing")
        return 0

    task_meta = load_task_meta(task_path)
    seq = 0
    run_id: str | None = None
    started_at = datetime.now(timezone.utc).isoformat()

    for raw in sys.stdin:
        sys.stdout.write(raw)
        sys.stdout.flush()
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue

        incoming_run_id = evt.get("run_id")
        if incoming_run_id and run_id is None:
            run_id = incoming_run_id
            override_title = os.environ.get("RUN_TITLE")
            pr_number = os.environ.get("PR_NUMBER")
            pr_url = os.environ.get("PR_URL")
            commit_sha = os.environ.get("COMMIT_SHA")
            # Keep the fixture task_id in the DB column so the Supabase
            # auto-remediation trigger can resolve it to a real task.yaml.
            # The PR/commit linkage lives in the title + payload instead.
            fixture_task_id = task_meta.get("task_id")
            upsert_run(
                {
                    "run_id": run_id,
                    "task_id": fixture_task_id,
                    "title": override_title or task_meta.get("title"),
                    "mode": "treatment",
                    "verdict": "PENDING",
                    "adapter": "gemini",
                    "started_at": started_at,
                    "payload": {
                        "source": "demo-run-on-push",
                        "stream_started_at": started_at,
                        "pr_number": pr_number,
                        "pr_url": pr_url,
                        "commit_sha": commit_sha,
                        "fixture_task_id": fixture_task_id,
                    },
                }
            )
            sys.stderr.write(f"[mirror] upserted parent cbc_runs row {run_id}\n")

        if not run_id:
            continue

        seq += 1
        insert_event(
            {
                "run_id": run_id,
                "seq": seq,
                "kind": str(evt.get("type", "event")).upper().replace(".", "_"),
                "emitted_at": datetime.now(timezone.utc).isoformat(),
                "payload": evt,
            }
        )

        if evt.get("type") == "run.completed":
            patch_run(
                run_id,
                {
                    "verdict": evt.get("verdict") or "UNKNOWN",
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "source": "demo-run-on-push",
                        "stream_started_at": started_at,
                        "verdict": evt.get("verdict"),
                        "attempts_count": evt.get("attempts"),
                        "total_tokens": evt.get("total_tokens"),
                        "pr_number": os.environ.get("PR_NUMBER"),
                        "pr_url": os.environ.get("PR_URL"),
                        "commit_sha": os.environ.get("COMMIT_SHA"),
                    },
                },
            )
            sys.stderr.write(
                f"[mirror] run {run_id} patched to verdict={evt.get('verdict')}\n"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
