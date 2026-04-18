# Status

## Working Now

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated benchmark comparison is reproducible from one command.
- Treatment currently improves verified success rate on the checked-in curated subset.

## Evidence

- tests: `PYTHONPATH=src python3 -m pytest`
- benchmark: `./scripts/run_compare.sh`
- proof card path is emitted after each `run`

## Remaining Depth

- deeper verification runners are present but intentionally lightweight and non-blocking
- review/graph/API shells are implemented and can be deepened without moving trust logic
- live Codex tasks need real task specs that exercise `adapter: codex`
