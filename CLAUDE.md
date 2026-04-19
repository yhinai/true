# CLAUDE.md

Claude-specific guidance for working in this repository. Follows the push-forward workflow defined in [AGENTS.md](./AGENTS.md).

## Project

**CBC — Correct by Construction.** Verification-first control plane for Codex code generation. Deterministic verification, staged execution, bounded retries, proof artifacts.

## Tech Stack

- Python 3.11+, FastAPI, Pydantic v2
- Package manager: **uv** (never `pip` directly)
- Test: `uv run pytest`
- Lint: `uv run --with ruff ruff check`
- Storage: SQLite (`artifacts/cbc.sqlite3`)

## Key Paths

| Path | Purpose |
|------|---------|
| `src/cbc/main.py` | CLI entry (`cbc run`, `cbc compare`, `cbc review`, `cbc ci`, `cbc api`) |
| `src/cbc/controller/orchestrator.py` | `run_task` coordination, sequential + gearbox |
| `src/cbc/controller/run_state.py` | `RunState` model (iteration, history, failure context) |
| `src/cbc/controller/routing.py` | `route_after_verify` retry/complete/abort decision |
| `src/cbc/controller/ledger_factory.py` | `build_final_ledger` from state + attempts |
| `src/cbc/controller/gearbox_runner.py` | `run_gearbox_parallel` async candidate executor |
| `src/cbc/workspace/backends.py` | `WorkspaceBackend` protocol, `SandboxMode`, `LocalBackend` |
| `src/cbc/workspace/contree_adapter.py` | `ContreeWorkspace` (opt-in via `--extra contree`) |
| `src/cbc/verify/core.py` | `verify_workspace` — already parallelized via `ThreadPoolExecutor` |
| `src/cbc/model/codex_exec.py` | Codex CLI subprocess adapter (timeouts already enforced) |
| `src/cbc/storage/candidate_lineage.py` | `candidate_snapshots` table for gearbox branches |
| `fixtures/oracle_tasks/` | Golden tasks (calculator_bug, title_case_bug, slug_shell_bug) |
| `docs/superpowers/specs/` | Design specs |
| `docs/superpowers/plans/` | Implementation plans |

## CLI Flags

```
cbc run <task.yaml>
  --mode baseline|treatment|review       (default: treatment)
  --controller sequential|gearbox         (default: sequential)
  --sandbox local|contree                 (default: local)
  --agent codex|replay                    (optional)
  --json                                  (JSON output)
  --stream                                (stream events)
```

## Common Commands

```bash
# Fast test suite (excludes slow markers)
uv run pytest tests/ -m "not slow"

# Full suite with contree extras
uv run --extra contree --extra dev pytest tests/

# Smoke-test a treatment run
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml \
  --mode=treatment --json | jq '.verification.status'

# Gearbox parallel (requires live ConTree backend)
uv run --extra contree cbc run fixtures/oracle_tasks/calculator_bug/task.yaml \
  --mode=treatment --controller=gearbox --sandbox=contree --json

# Benchmark sequential vs parallel
uv run python scripts/bench_gearbox_parallel.py > reports/gearbox_speedup.json
```

## Git & Commit Rules

Follow [AGENTS.md](./AGENTS.md) verbatim. Additional constraints enforced by the commit hook:

- **Conventional commits:** `<type>(scope): <description>`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `chore`
- **Subject ≤ 50 characters.** The hook rejects longer subjects.
- **No AI attribution** in commit messages (no `Co-Authored-By: Claude`, no "Generated with Claude Code", etc.). Commits reflect human ownership.
- **No `--no-verify` / `--no-gpg-sign`** unless explicitly asked.
- **Do not amend published commits.** Create a new commit instead.
- **Stage specific files** (`git add <path>`) rather than `git add -A` to avoid staging artifacts.

Push-forward: after any verified change, commit and push. Don't leave verified work uncommitted.

## Verification Gate

Before committing any code change:

1. **Unit tests** for the changed module: `uv run pytest tests/<path> -v`
2. **Fast suite** if the change crosses boundaries: `uv run pytest tests/ -m "not slow"`
3. **Lint** on changed files: `uv run --with ruff ruff check <path>`
4. **Smoke test** if the change touches orchestration: `cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --json`

If verification fails, fix before committing.

### Pre-commit Hook

A `.pre-commit-config.yaml` runs ruff + fast pytest on every `git commit`. Once per clone:

```bash
uv tool install pre-commit
uv tool run pre-commit install
```

Manual run: `uv tool run pre-commit run --all-files`

## CI Auto-Refresh

On pull requests, CI runs `scripts/refresh_examples.py` and, if the example artifacts drift, auto-commits a `chore: refresh example snapshots` commit back to the PR branch. On direct pushes to `main` and on forked PRs, a stale snapshot still fails the build. This means schema changes to `RunLedger`/`CandidateResult` etc. no longer require manual artifact refreshes on PR branches.

## Sandboxing

Local mode (`--sandbox=local`) is the default and always available — uses `tempfile.mkdtemp` + `shutil.copytree` for workspace isolation.

ConTree mode (`--sandbox=contree`) requires the `contree` extra (`uv sync --extra contree`) and a reachable ConTree backend. The adapter lives in `src/cbc/workspace/contree_adapter.py`.

## Known Follow-ups

- `ContreeWorkspace.prepare_async` passes `files={"/work": base_dir}` — the SDK's `files=` expects file-level entries, not a directory. Needs directory walk before `--sandbox=contree` end-to-end works.
- Parallel gearbox candidates currently share one `workspace_lease.root`. Under local sandbox this is safe because gearbox runs sequentially there; under ConTree, per-candidate branch fan-out is still needed for real isolation.
- `asyncio.run` inside `run_task` blocks nested event loops. Fine for CLI callers; a future ASGI-driven caller will need refactoring.

## Reference Patterns Used

- Orchestrator role decomposition and iteration state: `opencolin/ralphwiggum`
- Sandboxed branching model: `opencolin/contree-skill`
- Parallel branching architecture: `opencolin/opencode-cloud`
