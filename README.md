# Correct by Construction

Correct by Construction is a verification-first control plane for coding agents.

The core idea is simple: staged execution, deterministic verification, and retry-with-evidence sit between an agent's claims and your repo.

## Status

- Headless product surface is live: CLI, FastAPI API, checked-in artifacts, and benchmark reports.
- Replay-backed baseline and treatment loops are complete and reproducible.
- `gearbox` exists as a treatment-only controller mode, but the checked-in controller benchmark currently keeps it opt-in.
- The additive zero-config path is live as `cbc solve`.
- The headless public contract is frozen at `2026-04-18.v2`.

## Install

Minimal install:

```bash
uv sync --extra dev
```

If you want chart image generation as well:

```bash
uv sync --extra dev --extra charts
```

## Fast Start

Run the deterministic smoke benchmark:

```bash
./scripts/run_compare.sh
```

Run a single treatment task:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
```

Run the additive zero-config path from the current repo:

```bash
PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --stream --json
```

## CLI Surface

Single-task runs:

```bash
./scripts/run_baseline.sh
./scripts/run_treatment.sh
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --controller gearbox
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/slugify_property_regression/task.yaml --mode treatment
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/price_format_property_regression/task.yaml --mode treatment
```

Dynamic intake:

```bash
PYTHONPATH=src python3 -m cbc.main solve "Add a /health endpoint that returns 200"
PYTHONPATH=src python3 -m cbc.main solve "Fix the Node status badge labels" --verify "node test_status.js"
```

Benchmarks and controller proof:

```bash
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_live_compare.sh
python3 scripts/run_compare.py
python3 scripts/run_controller_compare.py
```

POC:

```bash
./scripts/run_poc_compare.sh --sample-size 2 --seed 42 --repetitions 2
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
```

Review and CI:

```bash
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
PYTHONPATH=src python3 -m cbc.main ci fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

Headless utility commands:

```bash
PYTHONPATH=src python3 -m cbc.main trends --last 20
PYTHONPATH=src python3 -m cbc.main benchmark-artifact <benchmark_id> --json
python3 scripts/refresh_examples.py
```

## JSON And Streaming

The headless CLI supports machine-readable output on the main product surface:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --json
PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --json
PYTHONPATH=src python3 -m cbc.main compare --json
PYTHONPATH=src python3 -m cbc.main controller-compare --json
PYTHONPATH=src python3 -m cbc.main poc --json
PYTHONPATH=src python3 -m cbc.main review-workspace fixtures/oracle_tasks/calculator_bug/task.yaml /path/to/workspace --json
PYTHONPATH=src python3 -m cbc.main review-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
PYTHONPATH=src python3 -m cbc.main ci-artifact artifacts/examples/calculator_treatment/run_ledger.json --json
```

`run` and `solve` also support NDJSON lifecycle streaming:

```bash
PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --stream --json
PYTHONPATH=src python3 -m cbc.main solve "Add a /health endpoint that returns 200" --stream --json
```

## API

Start the API:

```bash
uv run cbc api
```

Routes:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
curl http://127.0.0.1:8000/benchmarks
curl http://127.0.0.1:8000/benchmarks/<benchmark_id>
```

## Benchmarks

Checked-in subsets:

- `benchmark-configs/curated_subset.yaml`: smallest deterministic smoke benchmark
- `benchmark-configs/expanded_subset.yaml`: wider replay benchmark with multi-file, property, and Node coverage
- `benchmark-configs/controller_subset.yaml`: sequential vs gearbox proof gate
- `benchmark-configs/demo_subset.yaml`: named three-task demo slice
- `benchmark-configs/live_codex.yaml`: live Codex benchmark lane
- `benchmark-configs/poc_live_codex.yaml`: POC comparison lane

Replay task bank now includes:

- single-file Python repairs
- multi-file propagation via `checkout_tax_propagation`
- two property-regression tasks
- a non-Python Node task via `status_badge_js_contract`

## Outputs

- transient run artifacts: `artifacts/runs/`
- transient benchmark reports: `reports/benchmarks/`
- checked-in examples: `artifacts/examples/` and `reports/examples/`
- dynamic oracle artifacts: `artifacts/dynamic_oracles/`
- SQLite run index: `artifacts/cbc.sqlite3`

## Verification

Full local verification sweep:

```bash
PYTHONPATH=src pytest -q
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
python3 scripts/refresh_examples.py
python3 -m compileall src tests scripts
```

## Docs

- [Demo](docs/DEMO.md)
- [Spec](docs/SPEC.md)
- [Runbook](docs/RUNBOOK.md)
- [Status](docs/STATUS.md)
- [Benchmark Plan](docs/BENCHMARK_PLAN.md)
- [Roadmap](plan.md)
