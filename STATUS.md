# Status

## Working Now

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated replay smoke comparison is reproducible from one command.
- Treatment currently improves verified success rate on the checked-in replay subset.
- A live `adapter: codex` lane now exists for end-to-end agent runs against the same verifier loop.
- Review and CI can now validate an existing workspace diff through the same verifier core.
- Python tasks now run a bounded structural check that can fail locally-valid but signature-broken changes.

## Evidence

- tests: `uv run --extra dev pytest`
- benchmark: `./scripts/run_compare.sh`
- python wrapper: `python3 scripts/run_compare.py`
- proof card path is emitted after each `run`
- review/CI artifact path is emitted after `review-workspace` and `ci`
- live Codex task path: `./scripts/run_live_codex.sh`
- live Codex compare path: `./scripts/run_live_compare.sh`

## Remaining Depth

- deeper verification runners are still intentionally lightweight and non-blocking outside the bounded structural path
- review/graph/API shells are implemented and now emit diff-aware review and CI artifacts without moving trust logic
- a checked-in live Codex benchmark lane now exists for calculator, title-case, and slug tasks
- live benchmark configs can now pin lane-specific Codex runtime knobs in checked-in YAML
- live task specs can also pin task-specific Codex runtime knobs in checked-in config
- the checked-in live lane is now standardized on `gpt-5.4`, `workspace-write`, `dangerously_bypass_approvals: false`, and `model_reasoning_effort="medium"`
- the checked-in live lane intentionally leaves `profile` unset so it does not rely on a local user profile name
