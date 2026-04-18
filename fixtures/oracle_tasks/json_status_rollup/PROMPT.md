Update `summary.json` so it is derived from `checks.json`.

Requirements:
- `total_checks` must equal the number of entries in `checks.json`.
- `passing_checks` must equal the number of checks whose `"status"` is `"pass"`.
- `failing_checks` must equal the number of checks whose `"status"` is `"fail"`.
- `verified` must be `true` only when `failing_checks` is `0`.
- Do not modify `checks.json`.
