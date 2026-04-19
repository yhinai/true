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

## PR-gated Workflow

You keep typing `git push origin main` as normal. Under the hood, a local pre-push hook reroutes the push through a feature branch + PR with CI-gated auto-merge — no extra steps.

### One-time install (per clone)

```bash
ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
```

After install, `git push origin main` will:

1. Create `pr/auto-YYYYmmdd-HHMMSS` at the commit you intended to push
2. Push that branch to origin
3. Open a PR against `main`
4. Arm auto-merge (`gh pr merge --auto --squash`)
5. Print a summary
6. Hard-stop the direct push (so your local `main` doesn't race ahead)

The commits land on `main` automatically once CI passes. You do nothing.

### Requirements

- `gh` CLI authenticated (`gh auth login`)
- The repository has branch protection configured so that a failing CI blocks the merge. Auto-merge without required checks merges immediately.

### Emergency override

```bash
ALLOW_DIRECT_MAIN_PUSH=1 git push origin main
```

Only use this when the PR-gated path is itself broken (e.g. GitHub outage, CI infrastructure failure). Not for "I'm in a hurry."

### Explicit helper (optional)

If you want to script the reroute without relying on the hook:

```bash
scripts/push-via-pr.sh [optional-slug]
```

Same end result; used from CI jobs or automation that doesn't invoke git hooks.

### Server-side belt-and-suspenders

`.github/workflows/auto-merge.yml` re-arms `--auto --squash` on every open same-repo PR whenever a PR event fires or a check suite completes successfully. This ensures auto-merge stays enabled even if the client-side `gh pr merge --auto` call happened before required checks were registered.

### Autonomous rebasing and conflict resolution

- **Auto-rebase:** `.github/workflows/auto-update-prs.yml` fires on every push to `main` and rebases any open PR that became `BEHIND`. No manual intervention.
- **Auto-resolve:** `.github/workflows/auto-resolve-conflicts.yml` runs every 10 minutes (and on-demand) against `DIRTY` PRs. Safe classes (`artifacts/examples/**`, `reports/**`, `docs/**/*.md`) are auto-resolved with `-X theirs`; anything else is labeled `conflict-needs-review` and left for a human.

### Dynamic test surface

`tests/auto/` contains parametrized tests that auto-discover the current
feature surface at collection time. When you add:

- a new Typer subcommand → `test_cli_subcommands.py` auto-smokes it
- a new `VerificationVerdict` enum value → `test_verdicts_routable.py` auto-checks routing
- a new `fixtures/oracle_tasks/<name>/` → `test_oracle_tasks_parsable.py` auto-validates it
- a new `benchmark-configs/*.yaml` → `test_benchmark_configs.py` auto-validates it

No test-file edits needed. CI coverage expands automatically with the feature surface.

### LLM-powered conflict resolution (optional)

When the safe-class auto-resolver labels a PR `conflict-needs-review`, a 15-minute
cron job at `.github/workflows/llm-conflict-resolver.yml` tries to resolve it via
OpenAI (gpt-4o-mini). Steps:

1. For each conflicted file, send the common ancestor + both sides to OpenAI
2. Write the proposed merge
3. **Run the full fast test suite as a gate**
4. If tests pass -> push + label `resolver-succeeded`
5. If tests fail -> label `resolver-failed` (human review)

Gated on `OPENAI_API_KEY` repo secret being set. If absent, the job skips cleanly.
Never commit or log the key.
### Daily regression detection

`.github/workflows/daily-benchmark.yml` fires at 06:00 UTC every day and on-demand:

1. Runs `run_compare.sh` + `run_controller_compare.sh`
2. Compares JSON results vs checked-in baselines in `reports/examples/*/comparison.json`
3. If `delta_verified_success_rate` dropped > 5pp or any task flipped VERIFIED → non-VERIFIED,
   opens a GitHub issue with label `regression,automated`
4. Otherwise exits clean

Fully hands-off. No human action unless a regression fires.

### LLM PR reviewer (advisory)

`.github/workflows/llm-pr-reviewer.yml` runs on every PR event against the same-repo
branches. It sends the git diff (excluding `artifacts/`, `reports/`, `*.json`, `uv.lock`)
to `gpt-4o-mini` with a strict high-signal prompt, then posts a single review comment
with a verdict + findings. It is **non-blocking** — auto-merge still depends on `test`
check. Gated on `OPENAI_API_KEY` secret; skips cleanly if unset.

### Scoped CI (dynamic per-change)
`.github/workflows/ci.yml` has a `scoped-test` job that uses `dorny/paths-filter` to
detect which module groups changed on a PR and runs only the relevant test subtrees
first. The full `test` job still runs — scoped is additive, not replacement. Gives
faster feedback on small changes without weakening the coverage gate.
On pushes to `main`, scoped is skipped; main always runs the full suite.
### Test scaffold generator

```bash
python3 scripts/gen_test_scaffold.py src/cbc/foo/new_module.py
# → writes tests/foo/test_new_module.py with a minimal import assertion
```

Idempotent; skips if the test file already exists. Useful when an agent adds a new module.
