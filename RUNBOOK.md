# Runbook

## Verify The Repo

```bash
uv run --extra dev pytest
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

## Run The Live Codex Comparison

```bash
./scripts/run_live_compare.sh
```
This uses the same orchestrator and deterministic verifier, but the benchmark file pins live Codex runtime settings in its `codex:` block instead of relying only on app defaults.

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

Task specs can set `adapter: codex` and omit replay behavior. Benchmark YAML can pin lane-level Codex runtime settings under `codex:`, and individual task specs can also include a checked-in `codex:` block to pin task-specific knobs such as `sandbox`, `model`, `profile`, `--config` overrides, and extra writable directories. The adapter in `src/cbc/model/codex_exec.py` uses `codex exec --json` plus a JSON output schema. Checked-in live task specs are available under `fixtures/oracle_tasks/*_codex/`, and a checked-in live comparison config is available at `benchmark-configs/live_codex.yaml`.
