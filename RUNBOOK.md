# Runbook

## Verify The Repo

```bash
PYTHONPATH=src python3 -m pytest
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

## Start The API

```bash
PYTHONPATH=src python3 -m cbc.main api
```

## Where Output Goes

- transient run artifacts: `artifacts/runs/`
- transient benchmark reports: `reports/benchmarks/`
- checked-in examples: `artifacts/examples/`, `reports/examples/`

## Switching To Live Codex

Task specs can set `adapter: codex` and omit replay behavior. The adapter in [src/cbc/model/codex_exec.py](/Users/alhinai/Desktop/TRUE/src/cbc/model/codex_exec.py) uses `codex exec --json` plus a JSON output schema.
