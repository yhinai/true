# Benchmark Plan

## Fairness Contract

- same checked-in task specs
- same workspace snapshots
- same replayed proposal stream per task
- same deterministic verifier
- only retry behavior changes between baseline and treatment

## Curated Subset

- [calculator bug](/Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/calculator_bug/task.yaml)
- [title case bug](/Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/title_case_bug/task.yaml)
- [slug shell bug](/Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/slug_shell_bug/task.yaml)

## Primary Metrics

- Verified Success Rate
- Unsafe Claim Rate
- Average Retries
- Average Elapsed Seconds

## Current Expected Outcome

On the checked-in replay benchmark, treatment outperforms baseline on Verified Success Rate while keeping the same task-level Unsafe Claim Rate.

## Command Path

```bash
./scripts/run_compare.sh
```
