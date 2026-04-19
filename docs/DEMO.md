# Demo

## Replay Demo

Use the smallest deterministic scoreboard path:

```bash
./scripts/run_compare.sh
```

This gives a replay-backed baseline vs treatment comparison and writes proof artifacts under `artifacts/runs/` plus a benchmark report under `reports/benchmarks/`.

## Headless Solve Demo

Run the additive zero-config intake path from inside a repo:

```bash
PYTHONPATH=src python3 -m cbc.main solve "Add a /health endpoint that returns 200" --stream --json
```

This emits NDJSON lifecycle events while the run is active and finishes with the run artifact payload.

## Controller Proof Demo

Run the sequential-vs-gearbox proof gate on the widened replay subset:

```bash
./scripts/run_controller_compare.sh
```

The checked-in recommendation should remain `sequential` unless the benchmark data shows a clear verified-success lift for `gearbox`.

## Simulated POC Demo

Run the credential-free raw-vs-CBC scoreboard:

```bash
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
```

This reuses replay-backed sibling task specs so anyone cloning the repo can exercise the POC path without a live Codex binary or API credentials.

## Expected Proof Points

- deterministic verification remains the source of truth
- treatment can recover from failed or unsafe first attempts
- gearbox stays opt-in unless the controller benchmark proves otherwise
- checked-in examples can be regenerated without hand-editing artifacts
