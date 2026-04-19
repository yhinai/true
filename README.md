# Correct by Construction

Correct by Construction (CBC) is a verification-first control plane for coding agents.

The core idea is simple: staged execution, deterministic verification, and retry-with-evidence sit between an agent's claims and your repo.

## Status

- Headless product surface is live: CLI, FastAPI API, checked-in artifacts, and benchmark reports.
- Replay-backed baseline and treatment loops are complete and reproducible.
- `gearbox` runs candidates in parallel under `--sandbox=contree`; sequential fallback remains the default.
- The additive zero-config path is live as `cbc solve`.
- The headless public contract is frozen at `2026-04-18.v2`.
- `main` is PR-gated: direct pushes are auto-rerouted through a branch + PR with CI-gated auto-merge.

## Install

Minimal install:

```bash
uv sync --extra dev
```

With chart image generation:

```bash
uv sync --extra dev --extra charts
```

With ConTree sandbox backend:

```bash
uv sync --extra dev --extra contree
```

## Fast Start

Run the deterministic smoke benchmark:

```bash
./scripts/run_compare.sh
```

Run a single treatment task:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
```

Run the additive zero-config path from the current repo:

```bash
PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --stream --json
```

## CLI Surface

Single-task runs:

```bash
./scripts/run_baseline.sh
./scripts/run_treatment.sh
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --controller gearbox
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/slugify_property_regression/task.yaml --mode treatment
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/price_format_property_regression/task.yaml --mode treatment
```

Flags on `cbc run`:

```
--mode baseline|treatment|review           (default: treatment)
--controller sequential|gearbox             (default: sequential)
--sandbox local|contree                     (default: local; contree requires --extra contree)
--agent codex|replay                        (default: per task.yaml)
--max-seconds-per-attempt <float>           (default: None; wall-clock budget per attempt)
--json                                      (structured JSON output on stdout)
--stream                                    (NDJSON lifecycle events)
```

Gearbox with opt-in parallel candidates via ConTree branches:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml \
    --mode treatment --controller gearbox --sandbox contree --json
```

Dynamic intake:

```bash
PYTHONPATH=src python3 -m cbc.main solve "Add a /health endpoint that returns 200"
PYTHONPATH=src python3 -m cbc.main solve "Fix the Node status badge labels" --verify "node test_status.js"
```

Benchmarks and controller proof:

```bash
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_live_compare.sh
python3 scripts/run_compare.py
python3 scripts/run_controller_compare.py
python3 scripts/bench_gearbox_parallel.py      # sequential vs parallel wall time
```

POC:

```bash
./scripts/run_poc_compare.sh --sample-size 2 --seed 42 --repetitions 2
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
```

Review and CI:

```bash
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
PYTHONPATH=src python3 -m cbc.main ci fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

Headless utility commands:

```bash
PYTHONPATH=src python3 -m cbc.main trends --last 20
PYTHONPATH=src python3 -m cbc.main benchmark-artifact <benchmark_id> --json
python3 scripts/refresh_examples.py
```

## JSON And Streaming

The headless CLI supports machine-readable output on the main product surface:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --json
PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --json
PYTHONPATH=src python3 -m cbc.main compare --json
PYTHONPATH=src python3 -m cbc.main controller-compare --json
PYTHONPATH=src python3 -m cbc.main poc --json
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace --json
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

`run` and `solve` also support NDJSON lifecycle streaming:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --stream --json
PYTHONPATH=src python3 -m cbc.main solve "Add a /health endpoint that returns 200" --stream --json
```

## Controller Architecture

`run_task` is a state-machine loop split across three role-scoped helpers:

- `cbc.controller.run_state.RunState` — iteration, history, failure context, per-attempt elapsed
- `cbc.controller.routing.route_after_verify` — returns `RETRY`/`COMPLETE`/`ABORT`
- `cbc.controller.ledger_factory.build_final_ledger` — assembles the final `RunLedger`

Gearbox candidates run in parallel via `asyncio.gather` when `--sandbox=contree`; each candidate gets its own ConTree branch off a shared base image so siblings cannot interfere. Snapshot lineage is persisted to the `candidate_snapshots` table in `artifacts/cbc.sqlite3`.

## Sandboxing

Local mode (`--sandbox=local`) is the default — `shutil.copytree` into a `tempfile.mkdtemp` staging directory. Always available.

ConTree mode (`--sandbox=contree`) wraps the `contree-sdk` for container-level isolation with Git-like branching. Opt-in:

```bash
uv sync --extra contree
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment --sandbox contree
```

`ContreeWorkspace` walks the workspace directory (skipping `.git`, `__pycache__`, `node_modules`, top-level dotfiles) and uploads file-by-file. Each gearbox candidate gets its own branch via `branch_async`.

## Standing Instructions

Drop a `program.md` at the repo root (or `.cbc/program.md`) to give every `cbc run` standing instructions. Per-task overrides live at `fixtures/oracle_tasks/<name>/program.md`. Global + per-task stack is injected into the coder prompt under `## Standing Instructions` and persisted in the final `RunLedger.program_text`.

```bash
echo "Prefer defensive coding. Use type hints everywhere." > program.md
```

## Wall-Clock Budget

Bound each attempt by wall time (beyond the existing `max_attempts` count-based budget):

```bash
cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --max-seconds-per-attempt 300
```

Attempts that exceed the budget are recorded with verdict `TIMED_OUT` and retried within budget. The deadline is checked at coder/verify boundaries — not mid-subprocess.

## API

Start the API:

```bash
uv run cbc api
```

Routes:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
curl http://127.0.0.1:8000/benchmarks
curl http://127.0.0.1:8000/benchmarks/<benchmark_id>
```

## Benchmarks

Checked-in subsets:

- `benchmark-configs/curated_subset.yaml`: smallest deterministic smoke benchmark
- `benchmark-configs/expanded_subset.yaml`: wider replay benchmark with multi-file, property, and Node coverage
- `benchmark-configs/controller_subset.yaml`: sequential vs gearbox proof gate
- `benchmark-configs/demo_subset.yaml`: named three-task demo slice
- `benchmark-configs/live_codex.yaml`: live Codex benchmark lane
- `benchmark-configs/poc_live_codex.yaml`: POC comparison lane

Replay task bank now includes:

- single-file Python repairs
- multi-file propagation via `checkout_tax_propagation`
- two property-regression tasks
- a non-Python Node task via `status_badge_js_contract`

## Outputs

- transient run artifacts: `artifacts/runs/`
- transient benchmark reports: `reports/benchmarks/`
- checked-in examples: `artifacts/examples/` and `reports/examples/`
- dynamic oracle artifacts: `artifacts/dynamic_oracles/`
- SQLite run index: `artifacts/cbc.sqlite3` (tables: `runs`, `candidate_snapshots`)

## Verification

Full local verification sweep:

```bash
PYTHONPATH=src pytest -q
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
python3 scripts/refresh_examples.py
python3 -m compileall src tests scripts
```

## Contributing Workflow

`main` is PR-gated. Direct pushes to `origin/main` are intercepted by a local pre-push hook and silently rerouted through a feature branch + PR with CI-gated auto-merge. You keep typing `git push origin main`; the system handles branching, PR creation, CI, and merge.

One-time install per clone:

```bash
ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
uv tool install pre-commit
uv tool run pre-commit install
```

After install, a typical iteration looks like:

```bash
git add src/... tests/...
git commit -m "feat(scope): short description"    # pre-commit runs ruff + fast pytest
git push origin main                               # hook reroutes to pr/auto-YYYYmmdd-HHMMSS
                                                   # PR opens, CI runs, auto-merges when green
```

What's wired server-side:

- **Branch protection on `main`**: required `test` status check, 0 approvals, linear history, no force push
- **Auto-merge** enabled on the repo with squash strategy
- **`.github/workflows/ci.yml`**: runs tests + auto-commits refreshed example snapshots back to PR branches when they drift (so schema changes don't require manual artifact regeneration)
- **`.github/workflows/auto-merge.yml`**: re-arms `gh pr merge --auto` on every open same-repo PR whenever a PR event fires or a check suite completes
- **`.github/workflows/ci-retry.yml`**: auto-retries a failed CI run once (self-healing for transient failures)

Commit format (enforced by the local commit-message hook):

- Conventional commits: `<type>(scope): <description>` — subjects ≤ 50 chars
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `chore`, `ci`
- No AI attribution lines in commit messages

Emergency override (for when the PR path itself is broken):

```bash
ALLOW_DIRECT_MAIN_PUSH=1 git push origin main
```

Branch protection will still reject this unless temporarily disabled server-side.

## Docs

- [Demo](docs/DEMO.md)
- [Spec](docs/SPEC.md)
- [Runbook](docs/RUNBOOK.md)
- [Status](docs/STATUS.md)
- [Benchmark Plan](docs/BENCHMARK_PLAN.md)
- [Roadmap](plan.md)
- [Agent conventions](AGENTS.md)
- [Claude-specific guidance](CLAUDE.md)
- Design specs: `docs/superpowers/specs/`
- Implementation plans: `docs/superpowers/plans/`
