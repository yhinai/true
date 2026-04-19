# Phase 1 — Orchestrator Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the 733-line `orchestrator.py` into coordination + state + role layers without changing behavior, so `run_task` reads like a table of contents and each step is unit-testable.

**Architecture:** Extract three artifacts from `orchestrator.py` — a `RunState` Pydantic model (iteration, history, failure_context), a `_route_after_verify` router function (retry/complete/abort), and a `_build_final_ledger` factory. `run_task` becomes pure coordination. Adopted from `ralphwiggum/src/models.py` and `flow.py:183-204`.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest, ruff. Uses existing `cbc.models` (`RunLedger`, `VerificationReport`, `VerificationVerdict`) and `cbc.controller.scoring.CandidateScoringEngine`.

**Scope note:** `_run_sequential_attempt` (lines 566–625) and `_run_gearbox_attempt` (lines 370–481) already exist. This plan extracts ONLY the state model, router, and ledger factory, and threads them through `run_task` (lines 76–252). Gearbox internals are untouched.

---

## File Structure

**New files:**
- `src/cbc/controller/run_state.py` — `RunState`, `IterationRecord`, `AttemptResult` Pydantic models
- `src/cbc/controller/routing.py` — `_route_after_verify` pure function
- `src/cbc/controller/ledger_factory.py` — `_build_final_ledger` pure function
- `tests/controller/test_run_state.py` — model tests
- `tests/controller/test_routing.py` — router tests
- `tests/controller/test_ledger_factory.py` — factory tests

**Modified files:**
- `src/cbc/controller/orchestrator.py` — `run_task` refactored to use new helpers; inline logic removed

---

### Task 1: Create `RunState` Model

**Files:**
- Create: `src/cbc/controller/run_state.py`
- Test: `tests/controller/test_run_state.py`

- [ ] **Step 1: Write the failing test**

Create `tests/controller/test_run_state.py`:

```python
from datetime import datetime
from pathlib import Path

from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import VerificationVerdict


def test_run_state_initial_defaults():
    state = RunState(
        task_id="t1",
        max_iterations=3,
        started_at=datetime(2026, 1, 1),
    )
    assert state.iteration == 0
    assert state.failure_context == []
    assert state.files_modified == set()
    assert state.iteration_history == []
    assert state.completed_at is None


def test_run_state_failure_context_caps_at_10():
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    for i in range(15):
        state.append_failure(f"err{i}")
    assert len(state.failure_context) == 10
    assert state.failure_context[0] == "err5"
    assert state.failure_context[-1] == "err14"


def test_record_iteration_appends_history_and_updates_modified():
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    record = IterationRecord(
        iteration=1,
        verdict=VerificationVerdict.FALSIFIED,
        files_modified=[Path("a.py"), Path("b.py")],
        error_summary="tests failed",
    )
    state.record_iteration(record)
    assert len(state.iteration_history) == 1
    assert state.iteration_history[0] is record
    assert state.files_modified == {Path("a.py"), Path("b.py")}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/controller/test_run_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cbc.controller.run_state'`

- [ ] **Step 3: Create `RunState` module**

Create `src/cbc/controller/run_state.py`:

```python
"""Run-level state container for the orchestrator loop."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cbc.models import VerificationVerdict


class IterationRecord(BaseModel):
    iteration: int
    verdict: VerificationVerdict
    files_modified: list[Path] = Field(default_factory=list)
    error_summary: str = ""


class AttemptResult(BaseModel):
    verdict: VerificationVerdict
    candidate_index: int | None = None
    error_summary: str = ""
    files_modified: list[Path] = Field(default_factory=list)


class RunState(BaseModel):
    task_id: str
    iteration: int = 0
    max_iterations: int
    failure_context: list[str] = Field(default_factory=list)
    files_modified: set[Path] = Field(default_factory=set)
    iteration_history: list[IterationRecord] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None

    def append_failure(self, summary: str) -> None:
        self.failure_context.append(summary)
        if len(self.failure_context) > 10:
            self.failure_context = self.failure_context[-10:]

    def record_iteration(self, record: IterationRecord) -> None:
        self.iteration_history.append(record)
        for path in record.files_modified:
            self.files_modified.add(path)
```

- [ ] **Step 4: Create `__init__.py` for tests**

If `tests/controller/` does not have `__init__.py`, create one (empty file).

Run: `ls tests/controller/__init__.py || touch tests/controller/__init__.py`

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/controller/test_run_state.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Lint check**

Run: `uv run ruff check src/cbc/controller/run_state.py tests/controller/test_run_state.py`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add src/cbc/controller/run_state.py tests/controller/test_run_state.py tests/controller/__init__.py
git commit -m "feat(controller): add RunState model for orchestrator loop"
```

---

### Task 2: Create `_route_after_verify` Router

**Files:**
- Create: `src/cbc/controller/routing.py`
- Test: `tests/controller/test_routing.py`

- [ ] **Step 1: Write the failing test**

Create `tests/controller/test_routing.py`:

```python
from datetime import datetime

from cbc.controller.routing import RouteDecision, route_after_verify
from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import VerificationVerdict


def _state_with_verdict(verdict: VerificationVerdict, iteration: int, max_iterations: int = 3) -> RunState:
    state = RunState(task_id="t1", max_iterations=max_iterations, started_at=datetime(2026, 1, 1))
    state.iteration = iteration
    state.record_iteration(IterationRecord(iteration=iteration, verdict=verdict))
    return state


def test_route_complete_on_verified():
    state = _state_with_verdict(VerificationVerdict.VERIFIED, iteration=1)
    assert route_after_verify(state) is RouteDecision.COMPLETE


def test_route_retry_on_falsified_under_budget():
    state = _state_with_verdict(VerificationVerdict.FALSIFIED, iteration=1, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.RETRY


def test_route_abort_when_budget_exhausted():
    state = _state_with_verdict(VerificationVerdict.FALSIFIED, iteration=3, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.ABORT


def test_route_abort_on_unproven_no_retry():
    state = _state_with_verdict(VerificationVerdict.UNPROVEN, iteration=1, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.ABORT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/controller/test_routing.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement router**

Create `src/cbc/controller/routing.py`:

```python
"""Decide what to do after a verification step."""

from __future__ import annotations

from enum import Enum

from cbc.controller.run_state import RunState
from cbc.models import VerificationVerdict


class RouteDecision(str, Enum):
    RETRY = "retry"
    COMPLETE = "complete"
    ABORT = "abort"


def route_after_verify(state: RunState) -> RouteDecision:
    if not state.iteration_history:
        return RouteDecision.ABORT
    latest = state.iteration_history[-1]
    if latest.verdict is VerificationVerdict.VERIFIED:
        return RouteDecision.COMPLETE
    if latest.verdict is VerificationVerdict.UNPROVEN:
        return RouteDecision.ABORT
    if state.iteration >= state.max_iterations:
        return RouteDecision.ABORT
    return RouteDecision.RETRY
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/controller/test_routing.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/cbc/controller/routing.py tests/controller/test_routing.py`
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add src/cbc/controller/routing.py tests/controller/test_routing.py
git commit -m "feat(controller): add route_after_verify decision function"
```

---

### Task 3: Create `_build_final_ledger` Factory

**Files:**
- Create: `src/cbc/controller/ledger_factory.py`
- Test: `tests/controller/test_ledger_factory.py`

- [ ] **Step 1: Read existing ledger assembly in orchestrator**

Read: `src/cbc/controller/orchestrator.py` lines 200–252 to see how `RunLedger` is currently assembled. The factory must produce the same shape. Also read `src/cbc/models.py` lines 228–251 for `RunLedger` fields.

- [ ] **Step 2: Write the failing test**

Create `tests/controller/test_ledger_factory.py`:

```python
from datetime import datetime
from pathlib import Path

from cbc.controller.ledger_factory import build_final_ledger
from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import (
    AttemptRecord,
    ProofCard,
    RunLedger,
    VerificationReport,
    VerificationVerdict,
)


def _state_verified() -> RunState:
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    state.iteration = 1
    state.record_iteration(
        IterationRecord(
            iteration=1,
            verdict=VerificationVerdict.VERIFIED,
            files_modified=[Path("a.py")],
        )
    )
    state.completed_at = datetime(2026, 1, 1, 0, 1)
    return state


def _minimal_attempt() -> AttemptRecord:
    # Fill the minimum required fields per AttemptRecord schema.
    return AttemptRecord(attempt_index=1, verdict=VerificationVerdict.VERIFIED)


def _minimal_verification() -> VerificationReport:
    return VerificationReport(verdict=VerificationVerdict.VERIFIED, checks=[])


def _minimal_proof() -> ProofCard:
    return ProofCard(task_id="t1", verdict=VerificationVerdict.VERIFIED)


def test_build_final_ledger_returns_run_ledger():
    state = _state_verified()
    ledger = build_final_ledger(
        state=state,
        attempts=[_minimal_attempt()],
        final_verification=_minimal_verification(),
        proof_card=_minimal_proof(),
    )
    assert isinstance(ledger, RunLedger)
    assert ledger.task_id == "t1"
    assert len(ledger.attempts) == 1
    assert ledger.verdict is VerificationVerdict.VERIFIED
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/controller/test_ledger_factory.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement the factory**

Create `src/cbc/controller/ledger_factory.py`:

```python
"""Factory that converts loop state into a final RunLedger."""

from __future__ import annotations

from cbc.controller.run_state import RunState
from cbc.models import AttemptRecord, ProofCard, RunLedger, VerificationReport


def build_final_ledger(
    *,
    state: RunState,
    attempts: list[AttemptRecord],
    final_verification: VerificationReport,
    proof_card: ProofCard,
) -> RunLedger:
    return RunLedger(
        task_id=state.task_id,
        verdict=final_verification.verdict,
        attempts=attempts,
        verification=final_verification,
        proof_card=proof_card,
        iterations=len(state.iteration_history),
        started_at=state.started_at,
        completed_at=state.completed_at,
        files_modified=sorted(str(p) for p in state.files_modified),
    )
```

**Note:** If `RunLedger` schema differs from the fields above, align to the actual shape in `cbc/models.py:228-251`. The test asserts only `task_id`, `attempts`, and `verdict`, so additional fields can be populated without breaking the test.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/controller/test_ledger_factory.py -v`
Expected: PASS (1 test)

If the test fails because `RunLedger` requires fields you did not supply, open `src/cbc/models.py:228-251`, add the missing fields (taking defaults from existing `orchestrator.py` ledger construction), and re-run.

- [ ] **Step 6: Lint**

Run: `uv run ruff check src/cbc/controller/ledger_factory.py tests/controller/test_ledger_factory.py`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add src/cbc/controller/ledger_factory.py tests/controller/test_ledger_factory.py
git commit -m "feat(controller): add build_final_ledger factory"
```

---

### Task 4: Thread `RunState` Through `run_task`

**Files:**
- Modify: `src/cbc/controller/orchestrator.py:76-252`

- [ ] **Step 1: Read current `run_task` fully**

Read `src/cbc/controller/orchestrator.py` lines 76–252. Note:
- The for-loop iterating over attempts
- Where `_run_gearbox_attempt` and `_run_sequential_attempt` are called
- Where the final `RunLedger` is constructed
- What goes into the persisted artifact

- [ ] **Step 2: Add imports**

At the top of `src/cbc/controller/orchestrator.py` (around line 25-39 where other cbc imports live), add:

```python
from cbc.controller.ledger_factory import build_final_ledger
from cbc.controller.routing import RouteDecision, route_after_verify
from cbc.controller.run_state import IterationRecord, RunState
```

- [ ] **Step 3: Construct `RunState` at the start of `run_task`**

Near the top of `run_task` (after staging, before the attempt loop — around line 92 after `workspace_lease` is created), insert:

```python
state = RunState(
    task_id=task.task_id,
    max_iterations=max_attempts,
    started_at=datetime.utcnow(),
)
```

Ensure `from datetime import datetime` is imported at the top if not already.

- [ ] **Step 4: Record each iteration inside the attempt loop**

Inside the `for attempt_index in range(1, max_attempts + 1):` loop body, after the attempt completes and verification is known, insert:

```python
state.iteration = attempt_index
state.record_iteration(
    IterationRecord(
        iteration=attempt_index,
        verdict=verification_report.verdict,
        files_modified=[Path(p) for p in changed_files],
        error_summary=_summarize_failure(verification_report) if verification_report.verdict != VerificationVerdict.VERIFIED else "",
    )
)
if verification_report.verdict != VerificationVerdict.VERIFIED:
    state.append_failure(_summarize_failure(verification_report))
```

Where `_summarize_failure` is either an existing helper or you can add a minimal one next to `_emit_event`:

```python
def _summarize_failure(report: VerificationReport) -> str:
    failed = [c.name for c in report.checks if not c.passed]
    return ", ".join(failed) if failed else "no failed checks reported"
```

- [ ] **Step 5: Replace `if/else` retry decision with `route_after_verify`**

Find the existing retry decision in the loop (likely around lines 190–199 using `should_retry` or comparing `verdict`). Replace with:

```python
match route_after_verify(state):
    case RouteDecision.COMPLETE:
        state.completed_at = datetime.utcnow()
        break
    case RouteDecision.ABORT:
        state.completed_at = datetime.utcnow()
        break
    case RouteDecision.RETRY:
        continue
```

Keep `should_retry` logic as a defensive check inside `RouteDecision.RETRY` only if it adds guardrails not covered by `route_after_verify` (e.g., budget resolver). Otherwise remove the `should_retry` call to avoid duplicate gating.

- [ ] **Step 6: Replace inline ledger construction with `build_final_ledger`**

Find the existing `RunLedger(...)` construction (after the loop, around lines 200+). Replace with:

```python
ledger = build_final_ledger(
    state=state,
    attempts=attempts,
    final_verification=verification_report,
    proof_card=proof_card,
)
```

Where `attempts`, `verification_report`, and `proof_card` are the existing local variables. If the factory call fails because `build_final_ledger` does not accept a needed field, add that field to `build_final_ledger` — never inline-construct `RunLedger` here.

- [ ] **Step 7: Run the existing controller test suite**

Run: `uv run pytest tests/ -k "controller or orchestrator or run_task" -v`
Expected: All existing tests pass. No new failures.

- [ ] **Step 8: Run the full test suite**

Run: `uv run pytest tests/`
Expected: Exit 0, no new failures.

- [ ] **Step 9: Run a smoke task end-to-end**

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --json > /tmp/smoke.json`
Expected: Exit 0. Inspect `/tmp/smoke.json` — verdict field present, iterations > 0.

- [ ] **Step 10: Lint**

Run: `uv run ruff check src/cbc/controller/orchestrator.py`
Expected: No new errors.

- [ ] **Step 11: Commit**

```bash
git add src/cbc/controller/orchestrator.py
git commit -m "refactor(controller): thread RunState and routing through run_task"
```

---

### Task 5: Shrink `run_task` by Deleting Replaced Inline Logic

**Files:**
- Modify: `src/cbc/controller/orchestrator.py`

- [ ] **Step 1: Identify leftover dead code**

Search `src/cbc/controller/orchestrator.py` for:
- Any inline construction of `RunLedger(...)` other than through `build_final_ledger`
- Any inline retry conditionals superseded by `route_after_verify`
- Any local lists tracking failure strings now managed by `state.failure_context`

- [ ] **Step 2: Remove each duplicate**

Delete only the inline duplicates found in Step 1. Do not refactor anything else.

- [ ] **Step 3: Run the full test suite**

Run: `uv run pytest tests/`
Expected: All tests pass.

- [ ] **Step 4: Check file size reduction**

Run: `wc -l src/cbc/controller/orchestrator.py`
Expected: Line count < 700 (was 733). If unchanged, you missed a duplicate.

- [ ] **Step 5: Smoke test again**

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --json > /tmp/smoke2.json && diff <(jq '.verdict' /tmp/smoke.json) <(jq '.verdict' /tmp/smoke2.json)`
Expected: Diff is empty (same verdict as Task 4 smoke).

- [ ] **Step 6: Commit**

```bash
git add src/cbc/controller/orchestrator.py
git commit -m "refactor(controller): remove inline logic superseded by run_state helpers"
```

---

## Phase 1 Exit Criteria

- `src/cbc/controller/run_state.py`, `routing.py`, `ledger_factory.py` exist with tests
- All existing tests still pass (`uv run pytest tests/`)
- `cbc run` on `calculator_bug` produces the same verdict as before
- `src/cbc/controller/orchestrator.py` line count strictly less than 733
- `route_after_verify` has a direct unit test for each of its three return values
