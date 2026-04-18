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
- replay-backed fixtures for reproducible benchmarks
- Codex adapter wired through `codex exec --json --output-schema`
- deterministic verification via pytest, shell oracles, and lightweight gates
- SQLite-backed run and benchmark index
- proof cards, ledgers, compare reports, and scoreboard output

Quick start:

```bash
PYTHONPATH=src python3 -m pytest
./scripts/run_compare.sh
./scripts/run_treatment.sh
```

Key docs:
- [SPEC.md](/Users/alhinai/Desktop/TRUE/SPEC.md)
- [RUNBOOK.md](/Users/alhinai/Desktop/TRUE/RUNBOOK.md)
- [STATUS.md](/Users/alhinai/Desktop/TRUE/STATUS.md)
- [BENCHMARK_PLAN.md](/Users/alhinai/Desktop/TRUE/BENCHMARK_PLAN.md)
