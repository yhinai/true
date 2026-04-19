# CBC Orchestrator Evolution — ConTree + Ralph + Branching Gearbox

**Date:** 2026-04-18
**Status:** Draft (awaiting implementation plan)
**References:**
- `opencolin/ralphwiggum` (Python/CrewAI) — role decomposition pattern
- `opencolin/contree-skill` (MCP + Python SDK) — sandboxed branching backend
- `opencolin/opencode-cloud` (TypeScript/Cloudflare Workers) — parallel branching architecture

---

## Motivation

CBC's core orchestration logic lives in `src/cbc/controller/orchestrator.py` (733 lines). `run_task` currently handles:

1. Workspace staging
2. Budget resolution
3. Retry loop iteration
4. Gearbox branching logic
5. Candidate selection
6. Artifact saving
7. Diff summaries

This monolithic shape blocks three improvements identified in prior analysis:

- **Parallel verification** — checks in `verify/core.py` run sequentially
- **Subprocess safety** — `model/codex_exec.py` subprocess calls lack timeouts or sandboxing
- **Testability** — single-attempt vs gearbox branching logic is tangled, hard to unit-test

Three reference repos provide complementary patterns to address these gaps without redesigning CBC from scratch.

---

## Design Overview — Three Phases

Each phase is independently shippable. Later phases depend on earlier ones.

| Phase | Pattern Source | External Dep | Shipping Benefit |
|-------|----------------|--------------|------------------|
| 1. Orchestrator refactor | `ralphwiggum` | None | Readable `run_task`, testable roles |
| 2. ConTree workspace adapter | `contree-skill` | ConTree (opt-in) | Subprocess safety, sandboxing |
| 3. Branching gearbox | `opencode-cloud` | Phase 2 | Truly parallel candidates |

---

## Phase 1 — Orchestrator Refactor (ralphwiggum pattern)

### Problem

`orchestrator.run_task` is a 733-line function. Extracting unit tests for a single attempt requires understanding the entire file.

### Design

**Extract three explicit role wrappers** (no behavior change, just boundaries):

- **Planner** — wraps existing `roles/planner.py` + prompt assembly
- **Coder** — wraps existing `model/codex_exec.py` invocation
- **Verifier** — wraps existing `verify/core.py` invocation

**Add `RunState` Pydantic model** (inspired by `ralphwiggum/src/models.py:62-151`):

```python
class RunState(BaseModel):
    iteration: int = 0
    max_iterations: int
    current_task: TaskSpec
    verification_result: VerificationResult | None = None
    failure_context: list[str] = Field(default_factory=list, max_length=10)
    files_modified: set[Path] = Field(default_factory=set)
    iteration_history: list[IterationRecord] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None

    def record_iteration(self, record: IterationRecord) -> None: ...
```

**Extract pure step functions:**

- `_run_single_attempt(state, roles) -> AttemptResult`
- `_route_after_verify(state) -> Literal["retry", "complete", "abort"]`
- `_build_final_ledger(state, attempts) -> RunLedger`

**New file layout:**

```
src/cbc/controller/
├── orchestrator.py        # ~150 lines: coordination only
├── run_state.py           # RunState + IterationRecord + AttemptResult
└── roles_coordinator.py   # Planner/Coder/Verifier wrappers
```

**After refactor, `run_task` reads like a table of contents:**

```python
def run_task(task_spec, budget):
    state = RunState.initial(task_spec, budget)
    while state.iteration < state.max_iterations:
        attempt = _run_single_attempt(state, roles)
        state.record_iteration(attempt)
        match _route_after_verify(state):
            case "complete": break
            case "abort": break
            case "retry": state.iteration += 1
    return _build_final_ledger(state, attempts)
```

### Deliverables

- `orchestrator.py` reduced to ~150 lines (coordination only)
- `run_state.py` — state contract
- `roles_coordinator.py` — role wrappers
- Unit tests for `_route_after_verify` covering all three branches
- Unit tests for `_build_final_ledger` with mock state
- All existing integration tests pass (no behavior change)

### Non-goals for Phase 1

- No new functionality
- No ConTree integration
- No async/parallel execution
- No prompt changes

---

## Phase 2 — ConTree Workspace Adapter (contree-skill pattern)

### Problem

`workspace/staging.py` is a stub. Subprocess calls in `codex_exec.py` have no timeout, no sandboxing, and can hang indefinitely.

### Design

**Add `src/cbc/workspace/contree_adapter.py`** exposing a minimal interface that mirrors ConTree's Python SDK contract:

```python
class ContreeWorkspace:
    async def prepare(self, base_dir: Path, task_id: str) -> ImageId:
        """CHECK-PREPARE-EXECUTE. Returns reusable base image."""

    async def branch(self, image_id: ImageId) -> Branch:
        """Spawn child; O(1) fork via image.run(disposable=False)."""

    async def execute(
        self,
        branch: Branch,
        cmd: list[str],
        timeout: float,
    ) -> ExecResult:
        """Run with enforced timeout. Raises on TimeoutExpired."""

    async def diff(self, branch: Branch) -> str:
        """Return unified diff of branch vs parent."""
```

**Tag convention** (copying `contree-skill/SKILL.md:198-211`):

```
cbc/workspace/{task_id}:{version}
```

**CHECK-PREPARE-EXECUTE workflow:**

1. **CHECK** — `contree_list_images(tag_prefix="cbc/workspace/")` — zero-cost lookup
2. **PREPARE** (conditional) — `contree_import_image` + `contree_run(disposable=False)` for setup, then `contree_set_tag`
3. **EXECUTE** — `contree_run(..., directory_state_id=<rsynced>)`

**Feature flag on the CLI:**

```bash
cbc run task.yaml              # default: local subprocess (current)
cbc run task.yaml --sandbox=contree   # opt-in ConTree
```

**Graceful degradation:** If `contree` SDK is not installed and flag is set, error clearly. If flag is not set, no import of ConTree — zero new dependency at runtime for existing users.

### Deliverables

- `contree_adapter.py` with `ContreeWorkspace` class
- `--sandbox={local,contree}` CLI flag on `cbc run`
- Unit tests using the ConTree mock mode (SDK supports this per skill docs)
- Integration test: one oracle task runs end-to-end under `--sandbox=contree`
- Subprocess timeouts enforced in local mode too (separate subprocess-defense fix landing alongside)

### Non-goals for Phase 2

- No parallel candidates yet (Phase 3)
- No default switch to ConTree — stays opt-in
- No ConTree-specific artifact format; existing `RunLedger` used unchanged

---

## Phase 3 — Branching Gearbox (opencode-cloud pattern)

### Problem

Current gearbox runs candidates sequentially. Parallel attempts would require per-candidate filesystem isolation, which CBC doesn't currently provide.

### Design

**Each candidate = ConTree branch from the prepared base image.**

ConTree's invariant: siblings don't interfere. From `contree-skill/SKILL.md:283-292`:

```python
base = await image.run(shell="setup", disposable=False)
branch_a = await base.run(shell="candidate_a")  # base unchanged
branch_b = await base.run(shell="candidate_b")  # base still unchanged
```

**Map to CBC gearbox:**

```python
async def _run_gearbox_attempt(state, roles):
    base = await workspace.prepare(state.task_spec.root, state.task_id)
    branches = await asyncio.gather(*[
        _run_candidate(base, roles, candidate_idx=i)
        for i in range(state.candidate_count)
    ])
    return _select_candidate(branches)  # existing heuristic unchanged
```

**Store snapshot lineage in SQLite** (existing `storage/` layer):

```sql
CREATE TABLE candidate_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    parent_id TEXT,
    candidate_index INTEGER,
    verdict TEXT,
    created_at TIMESTAMP
);
```

Lineage design copied from `opencode-cloud/apps/worker/src/routes/branches.ts:304-322` — flat KV records, tree reconstructed on demand.

**Skip Yjs CRDT layer.** CBC is single-user CLI; no collab requirement. This is a deliberate non-feature.

**`_select_candidate` logic unchanged.** The existing tuple sort in `orchestrator.py` continues to pick the winner. Only the execution path becomes parallel.

### Deliverables

- Gearbox attempt function uses `asyncio.gather` over ConTree branches
- SQLite schema migration for `candidate_snapshots` table
- `cbc run --gearbox --sandbox=contree` runs candidates in parallel
- Measured: wall time reduction vs sequential gearbox on the expanded benchmark
- Existing `_select_candidate` tuple heuristic remains authoritative

### Non-goals for Phase 3

- No scoring-engine refactor yet (separate workstream, low-risk, can follow)
- No local-mode parallel gearbox (would require Python multiprocessing; out of scope)
- No cross-task snapshot reuse (each run re-prepares base image)

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 1 subtly changes behavior | Regressions | Keep all existing tests passing; no logic edits — only extractions |
| ConTree SDK instability | Phase 2/3 blocked | Feature-flagged; local mode stays default |
| Parallel gearbox races on shared state | Corrupted runs | ConTree invariant guarantees sibling isolation; lineage stored flat in SQLite |
| Scope creep (Phase 1 drags in unrelated cleanup) | Timeline | Strict: only moves code, never rewrites logic |

---

## Out of Scope (Deferred to Follow-up Specs)

These were raised in the earlier analysis but are orthogonal to the three phases above:

- Parallel verification inside `verify/core.py` (`asyncio.gather` over checks) — lands independently
- Rich UI progress spinners on the CLI — standalone UX polish
- Scoring Engine class replacing the hardcoded `_select_candidate` tuple — deferred until Phase 3 is stable

---

## Sequencing & Merge Plan

1. **Phase 1** — standalone branch, green CI, merge
2. **Phase 2** — depends on Phase 1 landing (imports `roles_coordinator`); adds opt-in flag
3. **Phase 3** — depends on Phase 2 stability (at least one week on main with no reported issues)

Each phase ships as a focused PR with its own test additions. No cross-phase refactoring.

---

## Success Criteria

- `orchestrator.py` < 200 lines (currently 733)
- `_route_after_verify` has direct unit tests
- `cbc run --sandbox=contree` completes an oracle task end-to-end
- `cbc run --gearbox --sandbox=contree` wall time is strictly less than sequential gearbox on the expanded benchmark
- No regression in existing integration tests across all three phases
