# Proof Card: json_status_rollup

- Verdict: `PASS`
- Suite: `treatment`
- Candidate source: `solution`
- Oracle kind: `local_validator`
- Oracle command: `python3 oracle.py`
- Allowed paths: `summary.json`
- Duration ms: `24`
- Started at: `2026-04-18T22:34:52+00:00`

## Prompt

Update `summary.json` so it is derived from `checks.json`.

Requirements:
- `total_checks` must equal the number of entries in `checks.json`.
- `passing_checks` must equal the number of checks whose `"status"` is `"pass"`.
- `failing_checks` must equal the number of checks whose `"status"` is `"fail"`.
- `verified` must be `true` only when `failing_checks` is `0`.
- Do not modify `checks.json`.

## Oracle stdout

```text
summary.json matches derived check counts.
```
