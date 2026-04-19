# Oracle Task Fixtures

Canonical task library for CBC runs. Each subdirectory is a self-contained fixture with `task.yaml`, a workspace, and (for replay tasks) a `replay.jsonl` trace.

## How to run

```bash
uv run cbc run fixtures/oracle_tasks/<task>/task.yaml --mode=treatment --json
```

Replace `<task>` with any directory name below. Append `--agent=codex` to use live Codex (requires Codex CLI + credentials); default is `replay` for the `_codex` variants too.

## Index

| Task | Language | Mode | Description |
|------|----------|------|-------------|
| `calculator_bug` | Python | replay | Fix addition in `calculator.py` |
| `calculator_bug_codex` | Python | codex | Same, but with live Codex |
| `live_codex_calculator` | Python | codex | Alternate live calculator fixture |
| `checkout_tax_propagation` | Python | replay | Multi-file structural change: propagate a taxed total signature across pricing and checkout |
| `greeting_text_patch` | Text | replay | Single-line greeting typo fix (golden) |
| `json_status_rollup` | JSON | replay | Repair a derived JSON summary (derived-state, golden) |
| `price_format_property_regression` | Python | replay | Fix price formatting and emit a regression artifact from a property case |
| `shell_banner_contract` | Shell | replay | Repair a shell-based verification banner (stdout / command-exit) |
| `slug_shell_bug` | Shell | replay | Fix slug rendering for shell validator |
| `slug_shell_bug_codex` | Shell | codex | Same, with live Codex |
| `slugify_property_regression` | Python | replay | Fix `slugify` and capture a regression test from a failing property case |
| `slugify_property_regression_codex` | Python | codex | Same, with live Codex |
| `status_badge_js_contract` | JavaScript | replay | Repair JS status badge labels (via Node) |
| `title_case_bug` | Python | replay | Fix title casing helper |
| `title_case_bug_codex` | Python | codex | Same, with live Codex |

### JSON-schema tasks

`tasks/` holds the declarative JSON task format indexed by `manifest.json`. Each entry corresponds to a benchmark scenario:

- `tasks/shell_exact_match/task.json`
- `tasks/pytest_divide_fix/task.json`
- `tasks/property_slugify/task.json`
- `tasks/shell_status_sanity/task.json`

## Task YAML schema

See `docs/TASK_YAML_SCHEMA.md` for field-by-field reference. Authoritative definition lives in `src/cbc/models.py::TaskSpec`.

## Adding a new task

1. Create `fixtures/oracle_tasks/<new_task>/` with:
   - `task.yaml` — metadata, prompt, oracles, required checks
   - `workspace/` — initial code tree the agent will edit
   - `replay.jsonl` (if `adapter: replay`) — recorded Codex trace
2. The dynamic test `tests/auto/test_oracle_tasks_parsable.py` will auto-discover it.
3. Run locally: `uv run cbc run fixtures/oracle_tasks/<new_task>/task.yaml --json`.
