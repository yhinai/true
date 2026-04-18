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
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)
    return connection
