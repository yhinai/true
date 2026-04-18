# Runbook

## Verify The Repo

```bash
uv run pytest
```

## Run One Treatment Task

```bash
./scripts/run_treatment.sh
```

## Run One Baseline Task

```bash
./scripts/run_baseline.sh
```

## Run The Curated Comparison

```bash
./scripts/run_compare.sh
```

## Run One Live Codex Task

```bash
./scripts/run_live_codex.sh
```

## Start The API

```bash
uv run cbc api
```

## Where Output Goes

- transient run artifacts: `artifacts/runs/`
- transient benchmark reports: `reports/benchmarks/`
- checked-in examples: `artifacts/examples/`, `reports/examples/`

## Switching To Live Codex

Task specs can set `adapter: codex` and omit replay behavior. The adapter in `src/cbc/model/codex_exec.py` uses `codex exec --json` plus a JSON output schema. A checked-in live task spec is available at `fixtures/oracle_tasks/calculator_bug_codex/task.yaml`.
