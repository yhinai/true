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

## Expanded Replay Subset

- `fixtures/oracle_tasks/calculator_bug/task.yaml`
- `fixtures/oracle_tasks/title_case_bug/task.yaml`
- `fixtures/oracle_tasks/slug_shell_bug/task.yaml`
- `fixtures/oracle_tasks/greeting_text_patch/task.yaml`
- `fixtures/oracle_tasks/json_status_rollup/task.yaml`
- `fixtures/oracle_tasks/shell_banner_contract/task.yaml`

## Primary Metrics

- Verified Success Rate
- Unsafe Claim Rate
- Average Retries
- Average Elapsed Seconds

## Current Expected Outcome

On the checked-in replay smoke benchmark, treatment outperforms baseline on Verified Success Rate while keeping the same task-level Unsafe Claim Rate.

## Phase 9 Proof Gate

The controller proof benchmark now compares treatment `sequential` versus treatment `gearbox` on the checked-in controller subset at `benchmark-configs/controller_subset.yaml`.

Current decision:
- keep `gearbox` opt-in
- keep `sequential` as the default treatment controller

Current evidence:
- no verified-success lift on the checked-in controller subset
- no unsafe-claim improvement on that subset
- higher average model-call spend for `gearbox`

## Live Codex Demo Candidate

- `benchmark-configs/live_codex.yaml`
- `fixtures/oracle_tasks/calculator_bug_codex/task.yaml`
- `fixtures/oracle_tasks/title_case_bug_codex/task.yaml`
- `fixtures/oracle_tasks/slug_shell_bug_codex/task.yaml`

## Command Path

```bash
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
python3 scripts/run_compare.py
python3 scripts/run_controller_compare.py
./scripts/run_live_compare.sh
./scripts/run_poc_compare.sh --sample-size 2 --seed 42
```

The comparison contract stays headless: CLI commands, API-readable artifacts, and checked-in reports use the same underlying run artifacts and verifier outputs.
The POC path now also emits paired arm-vs-arm scoreboard numbers with win/loss/tie counts, rate deltas, and 95% confidence intervals.
