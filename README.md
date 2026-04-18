# Correct by Construction

Correct by Construction is a verification-first control plane around Codex.

Baseline:
- one model attempt
- no external retry-with-evidence loop
- verdict comes from the first completion claim plus deterministic verification

Treatment:
- staged workspace
- deterministic oracle gate
- retry with concrete verifier evidence
- bounded attempts
- proof artifacts and honest verdicts

First working milestone:
- `Codex/replay -> staged workspace -> deterministic oracle -> retry -> proof card`

Single command path:

```bash
./scripts/run_compare.sh
```

Golden task:
- `fixtures/oracle_tasks/calculator_bug/task.yaml`

Current implementation:
- real CLI for `run`, `compare`, `review`, and `api`
- replay-backed fixtures for a reproducible smoke benchmark
- Codex adapter wired through `codex exec --json --output-schema`
- deterministic verification via pytest, shell oracles, and lightweight gates
- SQLite-backed run and benchmark index
- proof cards, ledgers, compare reports, and scoreboard output

Current benchmark honesty:
- the default checked-in benchmark is a replay smoke benchmark, not a live Codex benchmark
- live Codex execution is supported through `adapter: codex`
- the checked-in curated subset stays replay-backed for deterministic CI and local smoke runs
- a separate checked-in live suite is available at `benchmark-configs/live_codex_subset.yaml`

Live Codex lane:
- [benchmark-configs/live_codex.yaml](/Users/alhinai/Desktop/TRUE/benchmark-configs/live_codex.yaml)
- [fixtures/oracle_tasks/live_codex_calculator/task.yaml](/Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/live_codex_calculator/task.yaml)
- `./scripts/run_live_compare.sh`

Quick start:

```bash
uv run pytest
./scripts/run_compare.sh
./scripts/run_treatment.sh
uv run python scripts/run_compare.py
./scripts/run_live_codex.sh
./scripts/run_live_compare.sh
```

Key docs:
- [SPEC.md](SPEC.md)
- [RUNBOOK.md](RUNBOOK.md)
- [STATUS.md](STATUS.md)
- [BENCHMARK_PLAN.md](BENCHMARK_PLAN.md)

Live Codex task:

```bash
./scripts/run_live_codex.sh
```

Live Codex benchmark:

```bash
./scripts/run_live_compare.sh
```
