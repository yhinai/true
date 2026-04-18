# Status

## Working Now

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated replay smoke comparison is reproducible from one command.
- Treatment currently improves verified success rate on the checked-in replay subset.

## Evidence

- tests: `uv run pytest`
- benchmark: `./scripts/run_compare.sh`
- python wrapper: `uv run python scripts/run_compare.py`
- proof card path is emitted after each `run`
- live Codex task path: `./scripts/run_live_codex.sh`

## Remaining Depth

- deeper verification runners are present but intentionally lightweight and non-blocking
- review/graph/API shells are implemented and can be deepened without moving trust logic
- one live Codex task spec now exists, but the repo still needs a dedicated checked-in benchmark lane that exercises `adapter: codex` beyond the single calculator task
