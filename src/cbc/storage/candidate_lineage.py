"""Persistence for gearbox candidate snapshot lineage."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CandidateSnapshot:
    snapshot_id: str
    parent_id: str | None
    run_id: str
    candidate_index: int
    verdict: str


_SCHEMA = """
CREATE TABLE IF NOT EXISTS candidate_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    parent_id   TEXT,
    run_id      TEXT NOT NULL,
    candidate_index INTEGER NOT NULL,
    verdict     TEXT NOT NULL,
    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_snapshots_run ON candidate_snapshots(run_id);
"""


def init_lineage_schema(db: Path) -> None:
    with sqlite3.connect(db) as conn:
        conn.executescript(_SCHEMA)


def insert_snapshot(db: Path, snap: CandidateSnapshot) -> None:
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO candidate_snapshots "
            "(snapshot_id, parent_id, run_id, candidate_index, verdict) "
            "VALUES (?, ?, ?, ?, ?)",
            (snap.snapshot_id, snap.parent_id, snap.run_id, snap.candidate_index, snap.verdict),
        )


def list_snapshots_for_run(db: Path, run_id: str) -> list[CandidateSnapshot]:
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT snapshot_id, parent_id, run_id, candidate_index, verdict "
            "FROM candidate_snapshots WHERE run_id = ?",
            (run_id,),
        ).fetchall()
    return [
        CandidateSnapshot(
            snapshot_id=r[0],
            parent_id=r[1],
            run_id=r[2],
            candidate_index=r[3],
            verdict=r[4],
        )
        for r in rows
    ]
