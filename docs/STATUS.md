# Status

## Working Now

- Roadmap status: the implementation roadmap in `plan.md` is complete through Phase 10.
- `plan.md` sections 12 through 16 are reference sections, not additional implementation phases.

- Truthful baseline and treatment loops are implemented.
- Deterministic verification gates every completion claim.
- Treatment retries with concrete evidence.
- Curated replay smoke comparison is reproducible from one command.
- An expanded replay comparison now broadens the checked-in deterministic task bank beyond the smoke subset.
- Treatment currently improves verified success rate on the checked-in replay subset.
- A live `adapter: codex` lane now exists for end-to-end agent runs against the same verifier loop.
- Review and CI can now validate an existing workspace diff through the same verifier core.
- Python tasks now run a bounded structural check that can fail locally-valid but signature-broken changes.
- Python property checks can now emit counterexample artifacts and generated regression tests during the main retry loop.
- A bounded read-only explorer role now identifies likely targets and nearby tests before the coder runs, and that brief is persisted as a run artifact.
- A seeded POC harness now compares direct raw Codex against CBC baseline and treatment on a checked-in live task bank.
- The seeded POC harness now emits pairwise win/loss/tie summaries, rate deltas, and 95% confidence intervals so raw Codex and CBC can be compared numerically.
- A treatment-only gearbox mode now evaluates isolated primary and alternate coder candidates, selects one deterministically, and persists scheduler plus risk artifacts.
- The headless surface now includes JSON CLI outputs, streamed NDJSON lifecycle events, benchmark detail lookup via the API/store path, and SQLite-backed trends reporting.
- The headless public payloads are now versioned and frozen at `2026-04-18.v2` across run artifacts, review reports, CI reports, and benchmark comparison JSON.
- Python contract inspection is now real rather than placeholder-only: the verifier extracts recognized decorators from workspace modules and reports contract coverage honestly.
- CrossHair and mutation lanes are now task-configurable command runners instead of hard-coded stubs, while remaining optional and non-blocking.
- Property checks can now expand checked-in examples with bounded generated edge-case corpora before emitting counterexamples and regression artifacts.
- The Phase 9 proof gate is now answered on a checked-in controller subset: sequential remains the default treatment controller because gearbox adds model calls without improving verified success on that subset.
- Checked-in demo artifacts can now be regenerated through a deterministic refresh path instead of manual copy steps.
- The expanded replay bank now includes a multi-file propagation task, a second property-regression task, and a non-Python Node task.

## Evidence

- tests: `uv run --extra dev pytest`
- benchmark: `./scripts/run_compare.sh`
- expanded benchmark: `./scripts/run_expanded_compare.sh`
- python wrapper: `python3 scripts/run_compare.py`
- proof card path is emitted after each `run`
- review/CI artifact path is emitted after `review-workspace` and `ci`
- live Codex task path: `./scripts/run_live_codex.sh`
- live Codex compare path: `./scripts/run_live_compare.sh`
- automated raw-vs-CBC POC path: `./scripts/run_poc_compare.sh --sample-size 2 --seed 42`
- property-regression demo path: `PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/slugify_property_regression/task.yaml --mode treatment`
- gearbox demo path: `PYTHONPATH=src python3 -m cbc.main run fixtures/oracle_tasks/calculator_bug/task.yaml --controller gearbox`
- controller proof path: `./scripts/run_controller_compare.sh`
- json CLI path: `PYTHONPATH=src python3 -m cbc.main compare --json`
- controller json path: `PYTHONPATH=src python3 -m cbc.main controller-compare --json`
- POC json path: `PYTHONPATH=src python3 -m cbc.main poc --json`
- zero-config solve path: `PYTHONPATH=src python3 -m cbc.main solve "Fix the failing tests" --stream --json`
- trends path: `PYTHONPATH=src python3 -m cbc.main trends --last 20 --json`
- simulated POC path: `./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42`
- example refresh path: `python3 scripts/refresh_examples.py`

## Remaining Depth

- deeper verification runners are still intentionally lightweight and non-blocking outside the bounded structural path
- contract inspection is now concrete, but runtime contract enforcement and stronger symbolic reasoning remain opt-in rather than default trust gates
- review/graph/API shells are implemented and now emit diff-aware review and CI artifacts without moving trust logic
- a checked-in live Codex benchmark lane now exists for calculator, title-case, and slug tasks
- live benchmark configs can now pin lane-specific Codex runtime knobs in checked-in YAML
- live task specs can also pin task-specific Codex runtime knobs in checked-in config
- the checked-in live lane is now standardized on `gpt-5.4`, `workspace-write`, `dangerously_bypass_approvals: false`, and `model_reasoning_effort="medium"`
- the checked-in live lane intentionally leaves `profile` unset so it does not rely on a local user profile name
- the plan phases are now implemented end to end; the remaining work is post-plan maintenance, benchmark growth, and deeper optional verification rather than missing pipeline phases
- the replay benchmark bank now includes additional text, JSON, and shell fixtures beyond the smoke subset, but benchmark growth is still an open area for future expansion
