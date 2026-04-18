# Proof Card: shell_banner_contract

- Verdict: `PASS`
- Suite: `treatment`
- Candidate source: `solution`
- Oracle kind: `test_script`
- Oracle command: `sh oracle.sh`
- Allowed paths: `bin/report.sh`
- Duration ms: `9`
- Started at: `2026-04-18T22:34:52+00:00`

## Prompt

Fix `bin/report.sh` so a verifier can trust it.

Requirements:
- The script must exit with status `0`.
- The script must print exactly `verified:PASS`.
- Do not add extra output or trailing spaces.

## Oracle stdout

```text
Shell banner matches expected output.
```
