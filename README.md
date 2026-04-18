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
- real CLI for `run`, `compare`, `review`, `review-workspace`, `ci`, and `api`
- replay-backed fixtures for a reproducible smoke benchmark
- Codex adapter wired through `codex exec --json --output-schema`
- deterministic verification via pytest, shell oracles, bounded structural checks, and lightweight gates
- SQLite-backed run and benchmark index
- proof cards, ledgers, diff summaries, CI reports, compare reports, and scoreboard output

Current benchmark honesty:
- the default checked-in benchmark is a replay smoke benchmark, not a live Codex benchmark
- live Codex execution is supported through `adapter: codex`
- the checked-in curated subset stays replay-backed for deterministic CI and local smoke runs
- a separate checked-in live suite is available at `benchmark-configs/live_codex.yaml`
- live task specs can pin Codex runtime knobs through a checked-in `codex:` block instead of relying on local app defaults
- the checked-in live lane is standardized on `gpt-5.4`, `workspace-write`, and no approval bypass

Live Codex lane:
- [benchmark-configs/live_codex.yaml](benchmark-configs/live_codex.yaml)
- [fixtures/oracle_tasks/calculator_bug_codex/task.yaml](fixtures/oracle_tasks/calculator_bug_codex/task.yaml)
- [fixtures/oracle_tasks/title_case_bug_codex/task.yaml](fixtures/oracle_tasks/title_case_bug_codex/task.yaml)
- [fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml](fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml)
- Codex runtime is pinned in the benchmark file under `codex:`, with task-level `codex:` blocks keeping single-task live runs on the same `gpt-5.4` / `workspace-write` / no-bypass stance
- `./scripts/run_live_compare.sh`

Quick start:

```bash
uv run --extra dev pytest
./scripts/run_compare.sh
./scripts/run_treatment.sh
python3 scripts/run_compare.py
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

Review/CI validation against an existing workspace diff:

```bash
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
PYTHONPATH=src python3 -m cbc.main ci fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
```
