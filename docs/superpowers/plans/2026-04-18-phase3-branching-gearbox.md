# Phase 3 — Branching Gearbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `cbc run --controller=gearbox --sandbox=contree` execute all candidates in parallel using ConTree branches, with snapshot lineage persisted to SQLite, while the existing `CandidateScoringEngine.select` heuristic remains the winner picker.

**Architecture:** Each candidate becomes a ConTree branch from a single prepared base image (siblings don't interfere — ConTree invariant). `asyncio.gather` parallelizes candidate execution. Snapshot metadata (id, parent, candidate index, verdict) is written to a new SQLite table for lineage inspection. Winner selection is unchanged.

**Tech Stack:** Python 3.11+, asyncio, aiosqlite (or existing sync SQLite with a thread executor), existing `cbc.controller.scoring.CandidateScoringEngine`, ConTree SDK from Phase 2.

**Prerequisite:** Phase 2 merged and `--sandbox=contree` proven working on the oracle tasks.

---

## File Structure

**New files:**
- `src/cbc/storage/candidate_lineage.py` — snapshot lineage table schema + CRUD
- `src/cbc/controller/gearbox_runner.py` — `run_gearbox_parallel` async function
- `tests/controller/test_gearbox_runner.py` — async parallel-branch tests
- `tests/storage/test_candidate_lineage.py` — lineage CRUD tests

**Modified files:**
- `src/cbc/controller/orchestrator.py:370-481` — `_run_gearbox_attempt` delegates to `run_gearbox_parallel` when ContreeWorkspace is active
- `src/cbc/storage/runs.py` (or equivalent migration entry point) — registers the new table

---

### Task 1: Create `candidate_snapshots` SQLite Table

**Files:**
- Create: `src/cbc/storage/candidate_lineage.py`
- Test: `tests/storage/test_candidate_lineage.py`

- [ ] **Step 1: Read existing storage entry points**

Read `src/cbc/storage/runs.py` and `src/cbc/storage/artifacts.py` to identify:
- Where the SQLite connection is opened
- Whether there is a migration/schema init helper
- The existing table naming convention

- [ ] **Step 2: Write the failing test**

Create `tests/storage/test_candidate_lineage.py`:

```python
from pathlib import Path

from cbc.storage.candidate_lineage import (
    CandidateSnapshot,
    init_lineage_schema,
    insert_snapshot,
    list_snapshots_for_run,
)


def test_insert_and_list_snapshots(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_lineage_schema(db)
    snap = CandidateSnapshot(
        snapshot_id="s-1",
        parent_id=None,
        run_id="r-1",
        candidate_index=0,
        verdict="VERIFIED",
    )
    insert_snapshot(db, snap)
    results = list_snapshots_for_run(db, "r-1")
    assert len(results) == 1
    assert results[0].snapshot_id == "s-1"
    assert results[0].parent_id is None


def test_lineage_parent_child(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_lineage_schema(db)
    base = CandidateSnapshot(snapshot_id="base", parent_id=None, run_id="r-1", candidate_index=-1, verdict="UNPROVEN")
    child_a = CandidateSnapshot(snapshot_id="ca", parent_id="base", run_id="r-1", candidate_index=0, verdict="FALSIFIED")
    child_b = CandidateSnapshot(snapshot_id="cb", parent_id="base", run_id="r-1", candidate_index=1, verdict="VERIFIED")
    for s in (base, child_a, child_b):
        insert_snapshot(db, s)
    results = list_snapshots_for_run(db, "r-1")
    ids = sorted(s.snapshot_id for s in results)
    assert ids == ["base", "ca", "cb"]
    parents = {s.snapshot_id: s.parent_id for s in results}
    assert parents == {"base": None, "ca": "base", "cb": "base"}
```

- [ ] **Step 3: Create `tests/storage/__init__.py` if missing**

Run: `touch tests/storage/__init__.py`

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_candidate_lineage.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 5: Implement the lineage module**

Create `src/cbc/storage/candidate_lineage.py`:

```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_candidate_lineage.py -v`
Expected: PASS (2 tests).

- [ ] **Step 7: Register schema init at startup**

In `src/cbc/storage/runs.py` (or wherever the main DB is initialized on first run), call `init_lineage_schema(db_path)` alongside the existing tables. If there is no central init function, add this to whichever function opens the DB first.

- [ ] **Step 8: Run the full test suite**

Run: `uv run pytest tests/`
Expected: All pass.

- [ ] **Step 9: Lint**

Run: `uv run ruff check src/cbc/storage/candidate_lineage.py tests/storage/test_candidate_lineage.py`
Expected: No errors.

- [ ] **Step 10: Commit**

```bash
git add src/cbc/storage/candidate_lineage.py tests/storage/test_candidate_lineage.py tests/storage/__init__.py src/cbc/storage/runs.py
git commit -m "feat(storage): add candidate_snapshots lineage table"
```

---

### Task 2: Implement `run_gearbox_parallel`

**Files:**
- Create: `src/cbc/controller/gearbox_runner.py`
- Test: `tests/controller/test_gearbox_runner.py`

- [ ] **Step 1: Read current gearbox code**

Read `src/cbc/controller/orchestrator.py` lines 370–481 (`_run_gearbox_attempt`). Identify:
- How candidates are generated (one call to coder per candidate)
- How verification runs per candidate
- How `CandidateResult` objects are assembled
- Where `scoring_engine.select(...)` is called (around line 461)

- [ ] **Step 2: Write the failing test**

Create `tests/controller/test_gearbox_runner.py`:

```python
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from cbc.controller.gearbox_runner import ParallelCandidateSpec, run_gearbox_parallel


@pytest.mark.asyncio
async def test_runs_candidates_in_parallel(tmp_path: Path):
    call_order: list[str] = []

    async def fake_coder(idx: int) -> str:
        call_order.append(f"start-{idx}")
        await asyncio.sleep(0.05)
        call_order.append(f"end-{idx}")
        return f"cand-{idx}"

    async def fake_verify(cand: str) -> dict:
        return {"cand": cand, "verdict": "FALSIFIED" if cand.endswith("0") else "VERIFIED"}

    specs = [
        ParallelCandidateSpec(index=i, run_coder=lambda i=i: fake_coder(i), verify=fake_verify)
        for i in range(3)
    ]

    results = await run_gearbox_parallel(specs)

    # All three "start" events happen before any "end" event, i.e., real parallelism.
    assert call_order.index("end-0") > call_order.index("start-2")
    assert len(results) == 3
    assert {r["verdict"] for r in results} == {"FALSIFIED", "VERIFIED"}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/controller/test_gearbox_runner.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement `run_gearbox_parallel`**

Create `src/cbc/controller/gearbox_runner.py`:

```python
"""Parallel candidate execution for the gearbox controller."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class ParallelCandidateSpec:
    index: int
    run_coder: Callable[[], Awaitable[Any]]
    verify: Callable[[Any], Awaitable[dict]]


async def _run_one(spec: ParallelCandidateSpec) -> dict:
    candidate = await spec.run_coder()
    result = await spec.verify(candidate)
    return result


async def run_gearbox_parallel(specs: list[ParallelCandidateSpec]) -> list[dict]:
    return await asyncio.gather(*(_run_one(s) for s in specs))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/controller/test_gearbox_runner.py -v`
Expected: PASS (1 test).

- [ ] **Step 6: Lint**

Run: `uv run ruff check src/cbc/controller/gearbox_runner.py tests/controller/test_gearbox_runner.py`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add src/cbc/controller/gearbox_runner.py tests/controller/test_gearbox_runner.py
git commit -m "feat(controller): add run_gearbox_parallel for async candidate execution"
```

---

### Task 3: Wire Parallel Gearbox Into `_run_gearbox_attempt`

**Files:**
- Modify: `src/cbc/controller/orchestrator.py:370-481`

- [ ] **Step 1: Decide gating condition**

Parallel gearbox is opt-in: only activate when `sandbox is SandboxMode.CONTREE`. Local mode keeps the existing sequential path to avoid introducing Python multiprocessing complexity.

- [ ] **Step 2: Write an integration test stub**

Append to `tests/controller/test_gearbox_runner.py`:

```python
@pytest.mark.asyncio
async def test_gearbox_branches_share_parent_and_stay_isolated(tmp_path: Path):
    """Sibling branches do not interfere (ConTree invariant). Verified via mock."""
    base_state = {"counter": 0}

    async def fake_branch(idx: int, base: dict) -> dict:
        # Each branch gets a fresh copy; increments don't leak to siblings.
        local = dict(base)
        local["counter"] += idx + 1
        return local

    branches = await asyncio.gather(*(fake_branch(i, base_state) for i in range(3)))
    assert [b["counter"] for b in branches] == [1, 2, 3]
    assert base_state["counter"] == 0  # parent unchanged
```

- [ ] **Step 3: Run test to verify it passes (no code change yet, pure asyncio)**

Run: `uv run pytest tests/controller/test_gearbox_runner.py -v`
Expected: PASS (2 tests).

- [ ] **Step 4: Modify `_run_gearbox_attempt` to dispatch in parallel when ContreeWorkspace is active**

In `src/cbc/controller/orchestrator.py`, add at the top:

```python
import asyncio
from cbc.controller.gearbox_runner import ParallelCandidateSpec, run_gearbox_parallel
from cbc.storage.candidate_lineage import CandidateSnapshot, insert_snapshot
from cbc.workspace.backends import SandboxMode
```

Inside `_run_gearbox_attempt` (lines 370–481), add the parallel path. At the point where the existing function loops over candidates sequentially, branch:

```python
if workspace_lease.sandbox is SandboxMode.CONTREE:
    candidates = asyncio.run(
        _run_candidates_parallel(
            task=task,
            adapter=adapter,
            workspace_lease=workspace_lease,
            candidate_count=candidate_count,
            run_id=run_id,
            db_path=db_path,
        )
    )
else:
    # existing sequential loop stays exactly as-is
    candidates = _existing_sequential_candidates_loop(...)
```

Add a new private helper below:

```python
async def _run_candidates_parallel(
    *,
    task,
    adapter,
    workspace_lease,
    candidate_count: int,
    run_id: str,
    db_path,
) -> list[CandidateResult]:
    async def run_one(idx: int) -> CandidateResult:
        # Each candidate is a ConTree branch from workspace_lease.root.
        # Reuse existing run_coder + verify_workspace, wrapped in asyncio.to_thread
        # because they are currently sync.
        candidate = await asyncio.to_thread(
            run_coder,
            task=task,
            adapter=adapter,
            workspace=workspace_lease.root,
            candidate_index=idx,
        )
        verification = await asyncio.to_thread(
            verify_workspace,
            workspace_lease.root,
            task=task,
            changed_files=candidate.changed_files,
            claimed_success=True,
        )
        snapshot_id = f"{run_id}-cand-{idx}"
        insert_snapshot(
            db_path,
            CandidateSnapshot(
                snapshot_id=snapshot_id,
                parent_id=f"{run_id}-base",
                run_id=run_id,
                candidate_index=idx,
                verdict=verification.verdict.value,
            ),
        )
        return CandidateResult(
            candidate_index=idx,
            model_response=candidate,
            verification=verification,
            snapshot_id=snapshot_id,
        )

    specs = [run_one(i) for i in range(candidate_count)]
    return await asyncio.gather(*specs)
```

**Notes:**
- `CandidateResult` may not currently have a `snapshot_id` field — if so, add it in `cbc/models.py:197-208` with a default of `None` to keep the sequential path compatible.
- The exact parameters for `run_coder` and `verify_workspace` must match their actual signatures from reading `cbc/roles/coder.py` and `cbc/verify/core.py`. Adjust accordingly.
- The base snapshot `{run_id}-base` should be inserted before the candidates (see next step).

- [ ] **Step 5: Insert the base snapshot before candidates**

In `_run_gearbox_attempt`, before dispatching candidates, record the base:

```python
insert_snapshot(
    db_path,
    CandidateSnapshot(
        snapshot_id=f"{run_id}-base",
        parent_id=None,
        run_id=run_id,
        candidate_index=-1,
        verdict="UNPROVEN",
    ),
)
```

- [ ] **Step 6: Run a sequential-gearbox smoke (ensure no regression)**

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --controller=gearbox --json > /tmp/seq_gearbox.json`
Expected: Exit 0, verdict field present. No regression in local sequential mode.

- [ ] **Step 7: Run a parallel-gearbox smoke (if ConTree available)**

If `--extra contree` is installed and a ConTree backend is reachable:

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --controller=gearbox --sandbox=contree --json > /tmp/par_gearbox.json`
Expected: Exit 0, verdict matches sequential.

If ConTree is unavailable, this step is skipped — it's opt-in.

- [ ] **Step 8: Lint**

Run: `uv run ruff check src/cbc/controller/orchestrator.py`
Expected: No new errors.

- [ ] **Step 9: Full test suite**

Run: `uv run pytest tests/`
Expected: All pass.

- [ ] **Step 10: Commit**

```bash
git add src/cbc/controller/orchestrator.py src/cbc/models.py
git commit -m "feat(controller): run gearbox candidates in parallel under ContreeWorkspace"
```

---

### Task 4: Benchmark Sequential vs Parallel Gearbox

**Files:**
- Create: `scripts/bench_gearbox_parallel.py`

- [ ] **Step 1: Create the benchmark script**

Create `scripts/bench_gearbox_parallel.py`:

```python
"""Compare wall time for sequential vs parallel gearbox on one oracle task."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def run_once(task: Path, sandbox: str) -> dict:
    t0 = time.perf_counter()
    result = subprocess.run(
        [
            "uv", "run", "cbc", "run",
            str(task),
            "--mode=treatment",
            "--controller=gearbox",
            f"--sandbox={sandbox}",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    elapsed = time.perf_counter() - t0
    return {"elapsed": elapsed, "returncode": result.returncode, "stderr_tail": result.stderr[-500:]}


def main() -> int:
    task = Path("fixtures/oracle_tasks/calculator_bug/task.yaml")
    if not task.exists():
        print(f"Task fixture missing: {task}", file=sys.stderr)
        return 1
    seq = run_once(task, "local")
    par = run_once(task, "contree")
    report = {
        "sequential_seconds": seq["elapsed"],
        "parallel_seconds": par["elapsed"],
        "speedup": seq["elapsed"] / par["elapsed"] if par["elapsed"] > 0 else None,
        "sequential_rc": seq["returncode"],
        "parallel_rc": par["returncode"],
    }
    print(json.dumps(report, indent=2))
    if par["returncode"] != 0:
        return 2
    if par["elapsed"] >= seq["elapsed"]:
        print("WARNING: parallel did not beat sequential", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Record a baseline**

Run: `uv run python scripts/bench_gearbox_parallel.py > reports/gearbox_speedup.json`

Expected: JSON with `parallel_seconds < sequential_seconds` when ConTree is reachable. If ConTree is unavailable, the script returns a non-zero exit and the report reflects that — still commit the artifact for documentation.

- [ ] **Step 3: Commit the benchmark tooling**

```bash
git add scripts/bench_gearbox_parallel.py reports/gearbox_speedup.json
git commit -m "test(bench): compare sequential vs parallel gearbox wall time"
```

---

## Phase 3 Exit Criteria

- `candidate_snapshots` table exists in the main SQLite DB
- `cbc run --controller=gearbox --sandbox=local` is unchanged (regression-free)
- `cbc run --controller=gearbox --sandbox=contree` runs candidates concurrently via `asyncio.gather`
- Benchmark script records sequential vs parallel wall time
- Parallel path writes one base snapshot + N candidate snapshots per run
- `CandidateScoringEngine.select` continues to pick the winner — no scoring changes in this phase
- Full test suite green in both sandbox modes
