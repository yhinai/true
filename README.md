# Correct by Construction

> **Verification-first control plane for coding agents.** Staged execution, deterministic verification, bounded retries with evidence.

[![CI](https://github.com/yhinai/true/actions/workflows/ci.yml/badge.svg)](https://github.com/yhinai/true/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Contract 2026-04-18.v2](https://img.shields.io/badge/contract-2026--04--18.v2-green.svg)](src/cbc/headless_contract.py)

---

## The Idea

LLMs claim. CBC proves.

```
 ┌───────┐     ┌───────┐     ┌──────────┐     ┌─────────┐
 │ Task  │────▶│ Coder │────▶│ Verifier │────▶│ Verdict │
 └───────┘     └───────┘     └──────────┘     └─────────┘
                   ▲               │
                   │               ▼
                   └── Retry ◀─────┘
                       with failure context
```

Every change lands in a **staged workspace** (local copy or ConTree branch). Every claim is checked by an **oracle**: pytest, ruff, typecheck, contracts, hypothesis, mutation. Every outcome is recorded in a **reproducible ledger** (`RunLedger`) with snapshot lineage, timings, and the exact prompt the agent received.

Four verdicts; no subjective judgement:

| Verdict      | Meaning                                                 |
| ------------ | ------------------------------------------------------- |
| `VERIFIED`   | All required checks pass                                |
| `FALSIFIED`  | At least one required check fails                       |
| `UNPROVEN`   | Verification could not run to completion                |
| `TIMED_OUT`  | Attempt exceeded `--max-seconds-per-attempt` wall budget |

---

## Quickstart

```bash
# Install
uv sync --extra dev

# Run the smoke benchmark
./scripts/run_compare.sh

# Verify a single task
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment --json \
  | jq '.verification.status'
# => "VERIFIED"
```

Or zero-config intake:

```bash
uv run cbc solve "Fix the failing tests" --stream --json
```

---

## Features

### Core loop
- **Sandboxed staging** — `--sandbox local` (default, `shutil.copytree`) or `--sandbox contree` (container + Git-like branching)
- **Parallel verification** — oracle/lint/typecheck/contracts/hypothesis run concurrently in a thread pool
- **Bounded retries** — `max_attempts` count + optional `--max-seconds-per-attempt` wall-clock budget
- **Failure-context accumulation** — last N failures are fed back to the next planner iteration

### Controllers
- **Sequential** (default) — one candidate per attempt
- **Gearbox** — N candidates per attempt, runs them in **parallel ConTree branches** under `--sandbox contree`, picks the winner via tunable `CandidateScoringEngine` weights

### Agent instructions
- **Standing instructions** via `program.md` at repo root (global) + `fixtures/oracle_tasks/<name>/program.md` (per-task overrides) — stacked, injected into the coder prompt, persisted in the ledger

### Observability
- **NDJSON lifecycle events** via `--stream`
- **Machine-readable JSON** via `--json`
- **FastAPI surface** (`cbc api`) over runs and benchmarks
- **Rich spinners** on interactive TTYs (suppressed under `--json`/`--stream`)
- **Subprocess streaming** — Codex stdout parsed line-by-line, not blocked

### Contributing workflow
- **PR-gated `main`** — direct pushes are auto-rerouted into a feature branch + PR via a local pre-push hook
- **CI-gated auto-merge** — PRs merge themselves when `test` check is green (no human review step)
- **CI auto-refresh** — drifted example snapshots are auto-committed back to the PR branch
- **CI self-retry** — transient failures re-run once automatically

---

## Install

```bash
# Minimum
uv sync --extra dev

# With chart/benchmark image rendering
uv sync --extra dev --extra charts

# With ConTree sandbox backend
uv sync --extra dev --extra contree
```

Requires **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**.

---

## CLI Reference

### `cbc run <task.yaml>`

Run a single oracle task.

| Flag | Default | Purpose |
| --- | --- | --- |
| `--mode {baseline,treatment,review}` | `treatment` | Execution mode |
| `--controller {sequential,gearbox}` | `sequential` | Candidate strategy |
| `--sandbox {local,contree}` | `local` | Workspace isolation |
| `--agent {codex,replay}` | per task.yaml | Model adapter |
| `--max-seconds-per-attempt <float>` | None | Wall-clock budget per attempt |
| `--json` | off | Machine-readable output on stdout |
| `--stream` | off | NDJSON lifecycle events |

Examples:

```bash
# Default run
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment

# Gearbox with parallel candidates
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml \
    --controller gearbox --sandbox contree --json

# Aggressive wall-clock budget (proves TIMED_OUT verdict)
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml \
    --max-seconds-per-attempt 0.001 --json
```

### `cbc solve <prompt>`

Zero-config intake — infer the workspace and oracles from a natural-language prompt.

```bash
uv run cbc solve "Add a /health endpoint that returns 200"
uv run cbc solve "Fix the Node status badge labels" --verify "node test_status.js"
```

### `cbc compare` / `cbc controller-compare` / `cbc poc`

Benchmark comparison reports across checked-in configs.

```bash
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
python3 scripts/bench_gearbox_parallel.py    # sequential vs parallel wall time
```

### `cbc review` / `cbc ci`

Review or CI-gate an existing workspace or artifact.

```bash
uv run cbc review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
uv run cbc ci fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
uv run cbc review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
uv run cbc ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

### `cbc api`

Read-only FastAPI over runs and benchmarks.

```bash
uv run cbc api

curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
curl http://127.0.0.1:8000/benchmarks
curl http://127.0.0.1:8000/benchmarks/<benchmark_id>
```

---

## Architecture

```
src/cbc/
├── main.py                      CLI entry (Typer) — run, solve, compare, review, ci, api
├── api/                         FastAPI read surface
├── benchmark/                   Comparison & reporting
├── controller/
│   ├── orchestrator.py          run_task coordination (sequential + gearbox)
│   ├── run_state.py             RunState, IterationRecord, AttemptTimeout
│   ├── routing.py               route_after_verify → RETRY | COMPLETE | ABORT
│   ├── ledger_factory.py        build_final_ledger
│   ├── gearbox_runner.py        run_gearbox_parallel (asyncio.gather)
│   ├── scoring.py               CandidateScoringEngine + tunable CheckWeights
│   ├── budgets.py               Retry budget resolution
│   └── retries.py               should_retry guard
├── model/
│   ├── codex_exec.py            Codex CLI subprocess adapter (streaming + timeout)
│   ├── replay.py                Replay model adapter
│   └── prompts.py               Prompt assembly + program.md injection
├── prompts/
│   └── program_loader.py        Global + per-task program.md stacking
├── roles/                       coder, explorer, planner, reviewer, risk_worker
├── verify/core.py               verify_workspace — parallel ThreadPoolExecutor
├── workspace/
│   ├── backends.py              WorkspaceBackend protocol, SandboxMode, LocalBackend
│   ├── contree_adapter.py       ContreeWorkspace (file-walk upload + branch_async)
│   └── staging.py               create_workspace_lease / _async
└── storage/
    ├── artifacts.py             Per-run artifact directory
    ├── runs.py                  SQLite run index
    └── candidate_lineage.py     candidate_snapshots table
```

**Key types** (`src/cbc/models.py`):
- `TaskSpec` — task definition + optional `max_wall_seconds_per_attempt`
- `RunLedger` — final artifact, includes `program_text`, `attempts`, `verification`, `proof_card`
- `CandidateResult` — one gearbox candidate, includes `snapshot_id`
- `VerificationVerdict` — `VERIFIED | FALSIFIED | UNPROVEN | TIMED_OUT`

---

## Benchmarks

Checked-in benchmark configs:

| Config | Purpose |
| --- | --- |
| `benchmark-configs/curated_subset.yaml` | Smallest deterministic smoke |
| `benchmark-configs/expanded_subset.yaml` | Multi-file, property, Node coverage |
| `benchmark-configs/controller_subset.yaml` | Sequential vs gearbox proof |
| `benchmark-configs/demo_subset.yaml` | Three-task demo slice |
| `benchmark-configs/live_codex.yaml` | Live Codex lane |
| `benchmark-configs/poc_live_codex.yaml` | POC comparison lane |

Replay task bank covers single-file Python repairs, multi-file propagation (`checkout_tax_propagation`), property regressions, and a non-Python Node task (`status_badge_js_contract`).

---

## Outputs

| Location | Content |
| --- | --- |
| `artifacts/runs/<run_id>/` | Per-run ledger, retry transcript, verification report |
| `artifacts/examples/` | Checked-in reference runs (schema-gated by CI) |
| `artifacts/dynamic_oracles/` | Dynamic intake oracle artifacts |
| `artifacts/cbc.sqlite3` | Run index + `candidate_snapshots` lineage |
| `reports/benchmarks/<id>/` | Benchmark comparisons |
| `reports/examples/` | Checked-in benchmark reports |

---

## Verification Sweep

```bash
# Full local pipeline
uv run pytest -q
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
uv run python3 scripts/refresh_examples.py
python3 -m compileall src tests scripts
```

---

## Contributing

`main` is PR-gated — a local pre-push hook intercepts direct pushes and silently reroutes them through a feature branch + PR with CI-gated auto-merge. You keep typing `git push origin main`; the system does the rest.

### One-time setup per clone

```bash
ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
uv tool install pre-commit
uv tool run pre-commit install
```

### What happens on `git push origin main`

1. Pre-push hook intercepts the push
2. Creates `pr/auto-YYYYmmdd-HHMMSS` at your commit
3. Pushes that branch
4. Opens a PR against `main`
5. Arms `gh pr merge --auto --squash`
6. Blocks your direct push (so local `main` doesn't race ahead)
7. CI runs on the PR — tests, ruff, example-snapshot auto-refresh
8. When CI is green, GitHub auto-squashes the PR onto `main`

### Commit format

Enforced by a local commit-message hook:

- Conventional commits: `<type>(scope): <description>`
- Subject ≤ 50 characters
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `chore`, `ci`
- No AI attribution in commit messages

### Emergency override

```bash
ALLOW_DIRECT_MAIN_PUSH=1 git push origin main
```

Branch protection on the server will still reject the push unless disabled; use for hook-path failures only.

### Server-side workflows

- [`ci.yml`](.github/workflows/ci.yml) — tests + auto-commit refreshed snapshots on PR branches
- [`auto-merge.yml`](.github/workflows/auto-merge.yml) — re-arms `gh pr merge --auto` belt-and-suspenders
- [`ci-retry.yml`](.github/workflows/ci-retry.yml) — re-runs failed jobs once automatically

---

## Status

- ✅ Headless public contract frozen at `2026-04-18.v2`
- ✅ CLI, FastAPI API, checked-in artifacts, benchmark reports
- ✅ Replay + live Codex adapters, both reproducible
- ✅ Sequential + gearbox controllers, gearbox parallel under ConTree
- ✅ Zero-config intake via `cbc solve`
- ✅ PR-gated silent-merge workflow on `main`

---

## Docs

- [Demo](docs/DEMO.md) — end-to-end walkthrough
- [Spec](docs/SPEC.md) — product specification
- [Runbook](docs/RUNBOOK.md) — operational procedures
- [Benchmark Plan](docs/BENCHMARK_PLAN.md) — benchmarking methodology
- [Status](docs/STATUS.md) — phase progress
- [Roadmap](plan.md) — long-range plan
- [Agent conventions](AGENTS.md) — repo push-forward workflow
- [Claude guidance](CLAUDE.md) — Claude-specific rules
- Design specs: [`docs/superpowers/specs/`](docs/superpowers/specs/)
- Implementation plans: [`docs/superpowers/plans/`](docs/superpowers/plans/)

---

## License

MIT. See [LICENSE](LICENSE).
