# Runbook

## Verify The Repo

```bash
uv run --extra dev pytest
```

## Run One Treatment Task

```bash
./scripts/run_treatment.sh
```

## Run A Zero-Config Solve

```bash
PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --stream --json
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

## Run The Expanded Replay Comparison

```bash
./scripts/run_expanded_compare.sh
```
This keeps the same deterministic replay contract as the smoke subset, but broadens the checked-in replay bank with text, JSON-rollup, and shell-banner repair tasks.

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

## Run The Simulated Raw-vs-CBC POC

```bash
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
```
This uses replay-backed sibling task specs so the full POC path works without live credentials.

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

## Refresh Checked-In Examples

```bash
python3 scripts/refresh_examples.py
```
This reruns the replay-backed demo tasks and benchmark reports, normalizes transient ids and local absolute paths, and rewrites the checked-in example bundles under `artifacts/examples/` and `reports/examples/`.

## Machine-Readable CLI Output

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --json
PYTHONPATH=src python3 -m cbc.main compare --json
PYTHONPATH=src python3 -m cbc.main controller-compare --json
PYTHONPATH=src python3 -m cbc.main poc --json
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

## Inspect Recent Trends

```bash
PYTHONPATH=src python3 -m cbc.main trends --last 20 --json
```

## Auto-Remediation Queue

Failed `cbc_runs` rows (`verdict IN ('FALSIFIED','TIMED_OUT')`) are automatically enqueued into `cbc_remediations` by the `cbc_runs_enqueue_remediation` trigger installed by `migrations/supabase/0002_cbc_remediations.sql`. Each queued row carries the `run_id`, `task_id`, and a resolved `task_path` (explicit via the optional `cbc_tasks` mapping, otherwise inferred from the convention `fixtures/oracle_tasks/<task_id>/task.yaml`). The `unique (run_id)` constraint guarantees a failed run is never remediated twice. A separate drainer, `scripts/remediate_dispatcher.py`, polls `status='queued'` rows and fires `cbc-remediate.yml` via the GitHub Actions REST API using `GH_TOKEN` and `GH_REPO`; it flips rows to `running` on successful dispatch and records `error` on failure. Dry-run with `python3 scripts/remediate_dispatcher.py --run-once --dry-run`; dispatch manually with `gh workflow run cbc-remediate.yml -f task_path=<path> -f remediation_id=<id>`; inspect status with `psql "$POSTGRES_URL_NON_POOLING" -c "select status, count(*) from cbc_remediations group by status"`.

## Switching To Live Codex

Task specs can set `adapter: codex` and omit replay behavior. Benchmark YAML can pin lane-level Codex runtime settings under `codex:`, and individual task specs can also include a checked-in `codex:` block to pin task-specific knobs such as `sandbox`, `model`, `profile`, `--config` overrides, and extra writable directories. The adapter in `src/cbc/model/codex_exec.py` uses `codex exec --json` plus a JSON output schema. Checked-in live task specs are available under `fixtures/oracle_tasks/*_codex/`, and a checked-in live comparison config is available at `benchmark-configs/live_codex.yaml`. The current checked-in standard is `model: gpt-5.4`, `sandbox: workspace-write`, `dangerously_bypass_approvals: false`, and `model_reasoning_effort="medium"`, while leaving `profile` unset intentionally.
