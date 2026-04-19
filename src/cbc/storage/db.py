from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  verdict TEXT NOT NULL,
  unsafe_claims INTEGER NOT NULL,
  elapsed_seconds REAL NOT NULL,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost_usd REAL,
  artifact_dir TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS benchmarks (
  benchmark_id TEXT PRIMARY KEY,
  report_dir TEXT NOT NULL,
  delta_verified_success_rate REAL NOT NULL,
  delta_unsafe_claim_rate REAL NOT NULL,
  created_at TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30.0)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(SCHEMA)
    _ensure_column(connection, "runs", "total_tokens", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "runs", "estimated_cost_usd", "REAL")
    return connection


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})")
    }
    if column in existing:
        return
    try:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError as exc:
        if "duplicate column name" not in str(exc).lower():
            raise
