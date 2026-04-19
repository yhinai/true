# CBC Autoresearch Patterns — `program.md` + Fixed-Time-Budget

**Date:** 2026-04-19
**Status:** Draft (awaiting implementation plan)
**Reference:** `karpathy/autoresearch` — `program.md` (human-authored agent instructions) and the fixed 5-minute experiment budget.

---

## Motivation

Karpathy's autoresearch has two borrowable patterns:

1. **`program.md`** — human-authored markdown that defines the agent's standing objectives and constraints. Inverts the workflow: humans write org-level guidance, agents write code.
2. **Fixed-time experiment budget** — every experiment runs for exactly 5 minutes. Forces comparable runs and bounds worst-case wall time.

Both map cleanly onto CBC, which already has a prompt pipeline (`build_coder_prompt`) and a retry loop (`run_task` + `_run_sequential_attempt` / `_run_gearbox_attempt`) but:

- No durable place for standing instructions beyond per-task prompts and per-role templates
- No wall-clock bound per attempt — only `max_attempts` (count-based) and a per-model-call timeout inside `codex_exec.py`

This spec adapts both patterns. No GPU, no PyTorch, no domain change — CBC stays a correctness tool.

---

## Scope

**In scope:**
- `program.md` loader with global + per-task stacking
- Injection into the coder prompt only
- Persistence of resolved program text into `RunLedger`
- Per-attempt wall-clock budget with a new `TIMED_OUT` verdict
- Router behavior and tests for the new verdict

**Out of scope:**
- Injecting program.md into reviewer or explorer roles (they don't use LLM prompts — they operate on artifacts)
- Total-run wall-clock budget (YAGNI; add later if needed)
- Interrupting mid-subprocess (coarse-grained checkpoints only)
- GPU/ML-specific work

---

## Part 1 — `program.md` Stacking

### Locations

- **Global:** `program.md` at repo root
- **Per-task:** `<task.workspace.parent>/program.md` (optional; each task directory)

Neither conflicts with existing files in this repo (verified). Nothing in `.gitignore` excludes them.

### Loader

New module: `src/cbc/prompts/program_loader.py`.

```python
def load_program(task_dir: Path, repo_root: Path) -> str:
    """Return the stacked program text.

    - If neither global nor per-task file exists, return "".
    - If only one exists, return its text (rstrip'd).
    - If both exist, return:
        <global>
        
        ---
        
        <per-task>

    Per-task comes second so it wins on conflict by position.
    """
```

### Injection

In `src/cbc/model/prompts.py::build_coder_prompt` (~line 52), prepend the resolved program text under a clear heading before the task prompt:

```
## Standing Instructions

<program_text>

---

## Task
<existing task prompt>
```

If `program_text` is empty, insert nothing (no heading, no separator).

Only `build_coder_prompt` gets this injection. `reviewer.py` and `explorer.py` do not use LLM prompts and are unaffected.

### Persistence

Extend `RunLedger` in `src/cbc/models.py` (line ~229 onward):

```python
class RunLedger(BaseModel):
    # ... existing 17 fields ...
    program_text: str | None = None   # NEW — resolved stacked text actually sent to coder
```

Thread a new `program_text` kwarg through `build_final_ledger` in `src/cbc/controller/ledger_factory.py`. Default `None` to preserve backward compatibility for all existing constructors.

### Resolution point

`run_task` in `src/cbc/controller/orchestrator.py` resolves the program text once, at run start, before entering the attempt loop. The same text is handed to every attempt — attempts do not re-read the file.

---

## Part 2 — Fixed-Time-Budget per Attempt

### New knob: `max_wall_seconds_per_attempt`

- **Type:** `float | None`
- **Default:** `None` (no wall-clock limit — current behavior)
- **Resolution order:** CLI flag > task.yaml > default

Concrete placements:

- CLI: `cbc run ... --max-seconds-per-attempt 300` in `src/cbc/main.py`
- Task schema: optional `max_wall_seconds_per_attempt: float | None` field on `TaskSpec` in `src/cbc/models.py:109-133`
- State: field of the same name on `RunState` in `src/cbc/controller/run_state.py`

### Enforcement

Two checkpoints per attempt, inside the orchestrator:

1. Right after `run_coder` returns
2. Right before `verify_workspace` runs

If `time.monotonic() - attempt_started_at > max_wall_seconds_per_attempt`, raise `AttemptTimeout(elapsed)` and record the attempt with verdict `TIMED_OUT`.

This is coarse-grained by design — no process interruption mid-subprocess. Cleanup stays simple.

### New verdict: `TIMED_OUT`

Extend `VerificationVerdict` enum in `src/cbc/models.py:22-25`:

```python
class VerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    UNPROVEN = "UNPROVEN"
    TIMED_OUT = "TIMED_OUT"   # NEW
```

### Router update

`route_after_verify` in `src/cbc/controller/routing.py` treats `TIMED_OUT` exactly like `FALSIFIED`:

- Retry if iteration < max_iterations
- Abort if budget exhausted

Mirror of the UNPROVEN fix we already have. No branching logic needed.

### Per-attempt elapsed persistence

Extend `IterationRecord`:

```python
class IterationRecord(BaseModel):
    iteration: int
    verdict: VerificationVerdict
    elapsed_seconds: float = 0.0   # NEW
    files_modified: list[Path] = Field(default_factory=list)
    error_summary: str = ""
```

The orchestrator sets `elapsed_seconds = time.monotonic() - attempt_started_at` when recording each iteration. Feeds the existing `state.iteration_history` and flows into `RunLedger` via the existing pipeline — no other top-level ledger fields needed.

### Gearbox interaction

Inside `_run_gearbox_attempt`, each candidate gets its own deadline. The attempt's budget bounds the slowest candidate (via `asyncio.gather` on ConTree or sequential checkpoint otherwise). No new per-candidate config — candidates share `max_wall_seconds_per_attempt`.

### Interaction with `max_attempts`

Unchanged. Both caps are active simultaneously; whichever trips first wins. Wall-clock timeout → `TIMED_OUT` → retry → fresh budget on next attempt.

---

## File Structure

**New files:**
- `src/cbc/prompts/program_loader.py` — stacking loader
- `src/cbc/prompts/__init__.py` — package marker if missing
- `tests/prompts/test_program_loader.py` — neither / global-only / per-task-only / both-stacked
- `tests/controller/test_attempt_timeout.py` — per-attempt budget enforcement

**Modified files:**
- `src/cbc/model/prompts.py` — prepend program text in `build_coder_prompt`
- `src/cbc/models.py` — add `program_text` to `RunLedger`, add `TIMED_OUT` to `VerificationVerdict`, add `max_wall_seconds_per_attempt` to `TaskSpec`
- `src/cbc/controller/run_state.py` — add `max_wall_seconds_per_attempt`, extend `IterationRecord.elapsed_seconds`
- `src/cbc/controller/routing.py` — no logic change; router already returns RETRY for non-VERIFIED, non-VERIFIED-exhausted states; confirm coverage via new tests
- `src/cbc/controller/ledger_factory.py` — thread `program_text` kwarg through
- `src/cbc/controller/orchestrator.py` — resolve program text at run start, enforce attempt deadline, record elapsed, pass program_text to ledger factory
- `src/cbc/main.py` — `--max-seconds-per-attempt` CLI flag
- `tests/controller/test_run_state.py` — assert `elapsed_seconds` default
- `tests/controller/test_routing.py` — add `TIMED_OUT` RETRY/ABORT cases

---

## Sequencing

Two independent workstreams, either order:

1. **`program.md` workstream** — loader + tests, injection, ledger field, task-spec wiring
2. **Timeout workstream** — `TIMED_OUT` enum, state/router plumbing, orchestrator deadline, CLI flag

Land them as two separate PRs to keep review focused. Each is independently shippable; neither depends on the other.

---

## Success Criteria

- `program.md` at repo root applies to every `cbc run` without any flag
- `fixtures/oracle_tasks/<name>/program.md` (when present) stacks after the global
- `program_text` in the saved `run_ledger.json` reflects the exact text the coder received
- `cbc run ... --max-seconds-per-attempt 1` on a task whose coder sleeps > 1s produces verdict `TIMED_OUT` and retries if budget remains
- Default behavior (no program.md, no `--max-seconds-per-attempt`) is byte-identical to current main
- All existing tests still pass

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `program.md` bloats the coder prompt and degrades Codex output | Lower quality code | Keep program.md short; log resolved text into ledger so regressions are auditable |
| Clock skew or monotonic-vs-wall mix-ups | Spurious timeouts | Use `time.monotonic()` exclusively; never `time.time()` |
| `TIMED_OUT` verdict breaks downstream artifact consumers | Parse failures | Enum extension is additive; consumers default to `UNPROVEN` on unknown verdicts (add a test) |
| Stacked `program.md` makes debugging confusing | Agent behavior opaque | Ledger records the resolved text — `jq '.program_text' run_ledger.json` is the source of truth |

---

## Out of Scope (deferred follow-ups)

- Injecting program.md into reviewer/explorer pipelines if they ever gain LLM-backed steps
- Total-run wall-clock budget (`max_wall_seconds_total`)
- Per-candidate timeouts inside the gearbox (currently inherits per-attempt)
- Mid-subprocess interruption (SIGTERM, process groups)
