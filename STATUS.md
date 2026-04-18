# Status

## Working Now

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated replay smoke comparison is reproducible from one command.
- Treatment currently improves verified success rate on the checked-in replay subset.
- A live `adapter: codex` lane now exists for end-to-end agent runs against the same verifier loop.

## Evidence

- tests: `uv run --extra dev pytest`
- benchmark: `./scripts/run_compare.sh`
- python wrapper: `python3 scripts/run_compare.py`
- proof card path is emitted after each `run`
- live Codex task path: `./scripts/run_live_codex.sh`
- live Codex compare path: `./scripts/run_live_compare.sh`

## Remaining Depth

- deeper verification runners are present but intentionally lightweight and non-blocking
- review/graph/API shells are implemented and can be deepened without moving trust logic
- a checked-in live Codex benchmark lane now exists for calculator, title-case, and slug tasks
- the next gap is pinning lane-specific Codex runtime knobs in checked-in config, rather than relying on app defaults
