# Runbook

## Verify The Repo

```bash
uv run --extra dev pytest
```

## Run One Treatment Task

```bash
./scripts/run_treatment.sh
```

## Run One Treatment Task With The Gearbox Controller

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --controller gearbox
```

## Run One Baseline Task

```bash
./scripts/run_baseline.sh
```

## Run The Curated Comparison

```bash
./scripts/run_compare.sh
```

## Run The Controller Proof Benchmark

```bash
./scripts/run_controller_compare.sh
```
This compares treatment `sequential` versus treatment `gearbox` on the checked-in controller subset and emits a persisted recommendation about whether gearbox should remain opt-in or become the default controller.

## Run The Live Codex Comparison

```bash
./scripts/run_live_compare.sh
```
This uses the same orchestrator and deterministic verifier, but the benchmark file pins live Codex runtime settings in its `codex:` block instead of relying only on app defaults. The checked-in live lane is standardized on `gpt-5.4`, `workspace-write`, and `dangerously_bypass_approvals: false`.
The checked-in live lane also standardizes on `model_reasoning_effort="medium"` and intentionally leaves `profile` unset so it does not depend on a local user profile name.

## Run The Automated Raw-vs-CBC POC

```bash
./scripts/run_poc_compare.sh --sample-size 2 --seed 42 --repetitions 2
```
This samples from a checked-in live task bank, runs a direct raw Codex arm plus CBC baseline and treatment, and writes a JSON/markdown comparison under `reports/poc/`.
The report now includes per-arm 95% confidence intervals plus paired scoreboards for `cbc_baseline vs raw_codex`, `cbc_treatment vs raw_codex`, and `cbc_treatment vs cbc_baseline`.

## Run One Live Codex Task

```bash
./scripts/run_live_codex.sh
```

## Review An Existing Workspace Diff

```bash
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
```

## Run A CI Gate Against An Existing Workspace Diff

```bash
PYTHONPATH=src python3 -m cbc.main ci fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
```
## Start The API

```bash
uv run cbc api
```

Available headless API routes:

- `GET /health`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /benchmarks`
- `GET /benchmarks/{benchmark_id}`

## Where Output Goes

- transient run artifacts: `artifacts/runs/`
- transient benchmark reports: `reports/benchmarks/`
- checked-in examples: `artifacts/examples/`, `reports/examples/`

## Machine-Readable CLI Output

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --json
PYTHONPATH=src python3 -m cbc.main compare --json
PYTHONPATH=src python3 -m cbc.main controller-compare --json
PYTHONPATH=src python3 -m cbc.main poc --json
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

## Switching To Live Codex

Task specs can set `adapter: codex` and omit replay behavior. Benchmark YAML can pin lane-level Codex runtime settings under `codex:`, and individual task specs can also include a checked-in `codex:` block to pin task-specific knobs such as `sandbox`, `model`, `profile`, `--config` overrides, and extra writable directories. The adapter in `src/cbc/model/codex_exec.py` uses `codex exec --json` plus a JSON output schema. Checked-in live task specs are available under `fixtures/oracle_tasks/*_codex/`, and a checked-in live comparison config is available at `benchmark-configs/live_codex.yaml`. The current checked-in standard is `model: gpt-5.4`, `sandbox: workspace-write`, `dangerously_bypass_approvals: false`, and `model_reasoning_effort="medium"`, while leaving `profile` unset intentionally.
