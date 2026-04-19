"""Drain ``cbc_remediations`` queue and dispatch cbc-remediate.yml workflows.

Polls the Supabase ``cbc_remediations`` table for rows with ``status='queued'``
and fires a GitHub Actions workflow_dispatch for each via the REST API.

Environment:
    POSTGRES_URL_NON_POOLING  Supabase Postgres connection string.
    GH_TOKEN                  GitHub token with ``actions:write`` scope.
    GH_REPO                   ``owner/repo`` for the dispatch target.
    GH_REF                    Git ref to dispatch against (default ``main``).
    GH_WORKFLOW               Workflow filename (default ``cbc-remediate.yml``).

Idempotency: rows with ``started_at IS NOT NULL`` are skipped. On a successful
dispatch the row flips to ``status='running'`` and ``started_at=now()``. On
failure the row stays ``queued`` and ``error`` is populated.

Usage:
    python3 scripts/remediate_dispatcher.py --run-once
    python3 scripts/remediate_dispatcher.py --run-once --dry-run
    python3 scripts/remediate_dispatcher.py --interval 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

try:
    import psycopg  # psycopg3
except ImportError:  # pragma: no cover - optional dependency surface
    psycopg = None  # type: ignore[assignment]


GITHUB_API = "https://api.github.com"


@dataclass
class QueuedRow:
    id: int
    run_id: str
    task_id: str
    task_path: str


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"error: missing required env var {name}", file=sys.stderr)
        sys.exit(2)
    return value


def _fetch_queued(conn) -> list[QueuedRow]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, run_id, task_id, task_path
            from cbc_remediations
            where status = 'queued' and started_at is null
            order by created_at asc
            """
        )
        return [QueuedRow(*row) for row in cur.fetchall()]


def _dispatch_workflow(
    repo: str,
    workflow: str,
    ref: str,
    token: str,
    task_path: str,
    remediation_id: int,
) -> None:
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow}/dispatches"
    payload = {
        "ref": ref,
        "inputs": {
            "task_path": task_path,
            "remediation_id": str(remediation_id),
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # 204 No Content is the documented success response.
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status not in (201, 202, 204):
            raise RuntimeError(f"unexpected status {resp.status}: {resp.read()!r}")


def _mark_running(conn, row_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update cbc_remediations
            set status = 'running', started_at = now(), error = null
            where id = %s and started_at is null
            """,
            (row_id,),
        )
    conn.commit()


def _mark_error(conn, row_id: int, message: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update cbc_remediations
            set error = %s
            where id = %s
            """,
            (message[:2000], row_id),
        )
    conn.commit()


def _reap_stuck(conn, *, stuck_minutes: int = 60, dry_run: bool = False) -> int:
    """Requeue ``running`` rows whose workflow likely crashed mid-flight.

    A remediation cycle tops out around 60 min of GHA wall time. Anything
    still ``running`` past that window is almost certainly a dead row; flip
    it back to ``queued`` so the next drain picks it up. Idempotent.
    """
    with conn.cursor() as cur:
        if dry_run:
            cur.execute(
                """
                select id, run_id
                from cbc_remediations
                where status = 'running'
                  and started_at is not null
                  and started_at < now() - make_interval(mins => %s)
                """,
                (stuck_minutes,),
            )
            stuck = cur.fetchall()
            for row_id, run_id in stuck:
                print(f"would reap id={row_id} run_id={run_id}")
            return len(stuck)
        cur.execute(
            """
            update cbc_remediations
            set status = 'queued',
                started_at = null,
                error = coalesce(error || '; ', '') ||
                        'reaped after ' || %s || 'min stuck in running'
            where status = 'running'
              and started_at is not null
              and started_at < now() - make_interval(mins => %s)
            returning id, run_id
            """,
            (stuck_minutes, stuck_minutes),
        )
        reaped = cur.fetchall()
    conn.commit()
    for row_id, run_id in reaped:
        print(f"reaped stuck row id={row_id} run_id={run_id}")
    return len(reaped)


def _drain_once(conn, *, dry_run: bool, repo: str, workflow: str, ref: str, token: str) -> int:
    # Reap first so anything crashed mid-flight flows back into the queue
    # we're about to drain.
    _reap_stuck(conn, dry_run=dry_run)
    rows = _fetch_queued(conn)
    if dry_run:
        print(f"would dispatch {len(rows)}")
        for row in rows:
            print(f"  id={row.id} run_id={row.run_id} task_path={row.task_path}")
        return len(rows)

    dispatched = 0
    for row in rows:
        try:
            _dispatch_workflow(repo, workflow, ref, token, row.task_path, row.id)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            _mark_error(conn, row.id, f"{type(exc).__name__}: {exc}")
            print(
                f"dispatch failed id={row.id} run_id={row.run_id}: {exc}",
                file=sys.stderr,
            )
            continue

        _mark_running(conn, row.id)
        dispatched += 1
        print(
            f"dispatched id={row.id} run_id={row.run_id} task_path={row.task_path}"
        )
    return dispatched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-once", action="store_true", help="Drain once and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Log queued rows without dispatching.")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval (seconds).")
    args = parser.parse_args()

    if psycopg is None:
        print("error: psycopg is required (uv pip install psycopg[binary])", file=sys.stderr)
        return 2

    db_url = _require_env("POSTGRES_URL_NON_POOLING")

    if args.dry_run:
        token = os.environ.get("GH_TOKEN", "")
        repo = os.environ.get("GH_REPO", "<unset>")
    else:
        token = _require_env("GH_TOKEN")
        repo = _require_env("GH_REPO")
    workflow = os.environ.get("GH_WORKFLOW", "cbc-remediate.yml")
    ref = os.environ.get("GH_REF", "main")

    with psycopg.connect(db_url) as conn:
        if args.run_once:
            _drain_once(conn, dry_run=args.dry_run, repo=repo, workflow=workflow, ref=ref, token=token)
            return 0

        while True:
            try:
                _drain_once(conn, dry_run=args.dry_run, repo=repo, workflow=workflow, ref=ref, token=token)
            except psycopg.Error as exc:
                print(f"database error: {exc}", file=sys.stderr)
            time.sleep(max(1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
