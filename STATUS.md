# Status

## Working Now

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated replay smoke comparison is reproducible from one command.
- Treatment currently improves verified success rate on the checked-in replay subset.

## Evidence

- tests: `PYTHONPATH=src python3 -m pytest`
- benchmark: `./scripts/run_compare.sh`
- python wrapper: `python3 scripts/run_compare.py`
- proof card path is emitted after each `run`

## Remaining Depth

- deeper verification runners are present but intentionally lightweight and non-blocking
- review/graph/API shells are implemented and can be deepened without moving trust logic
- live Codex tasks need a dedicated checked-in benchmark lane that exercises `adapter: codex`
