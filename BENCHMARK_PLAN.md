# Benchmark Plan

## Fairness Contract

- same checked-in task specs
- same workspace snapshots
- same replayed proposal stream per task
- same deterministic verifier
- only retry behavior changes between baseline and treatment

## Curated Subset

- `fixtures/oracle_tasks/calculator_bug/task.yaml`
- `fixtures/oracle_tasks/title_case_bug/task.yaml`
- `fixtures/oracle_tasks/slug_shell_bug/task.yaml`

## Primary Metrics

- Verified Success Rate
- Unsafe Claim Rate
- Average Retries
- Average Elapsed Seconds

## Current Expected Outcome

On the checked-in replay smoke benchmark, treatment outperforms baseline on Verified Success Rate while keeping the same task-level Unsafe Claim Rate.

## Late-Phase Open Question

The next benchmark question is no longer baseline versus treatment plumbing. It is whether treatment `--controller gearbox` earns its extra model calls versus sequential treatment on a bounded checked-in subset. That comparison should be treated as the Phase 9 proof gate before gearbox becomes the default controller.

## Live Codex Demo Candidate

- `benchmark-configs/live_codex.yaml`
- `fixtures/oracle_tasks/calculator_bug_codex/task.yaml`
- `fixtures/oracle_tasks/title_case_bug_codex/task.yaml`
- `fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml`

## Command Path

```bash
./scripts/run_compare.sh
python3 scripts/run_compare.py
./scripts/run_live_compare.sh
./scripts/run_poc_compare.sh --sample-size 2 --seed 42
```

The comparison contract stays headless: CLI commands, API-readable artifacts, and checked-in reports use the same underlying run artifacts and verifier outputs.
The POC path now also emits paired arm-vs-arm scoreboard numbers with win/loss/tie counts, rate deltas, and 95% confidence intervals.
