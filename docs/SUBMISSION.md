# Submission Notes

## Track

Testing & Debugging Code

## One-paragraph submission description

Axiom is a Python-first debugging agent for JetBrains ACP and the terminal. It takes a failing test, stacktrace, or bug report, proposes a minimal patch, derives `icontract` preconditions/postconditions, verifies them with CrossHair, and returns an Evidence Ledger with one honest verdict: `VERIFIED`, `FALSIFIED`, or `UNPROVEN`. The primary demo bug is a compact Totality violation, which makes the proof story short, concrete, and stage-friendly.

## Demo commands

- Core demo command: `make demo`
- Falsified witness path: `make demo-falsified`
- Unproven honesty path: `make demo-unproven`
- Optional Non-Contradiction path: `make demo-non-contradiction`
- Optional Identity path: `make demo-identity`
- ACP import smoke: `make verify-acp`
- Codex workflow smoke: `codex exec -C /Users/alhinai/Desktop/TRUE --skip-git-repo-check "Reply with exactly: codex-ok"`
- OpenAI smoke: `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py`

## Assets

- Screenshots directory: `docs/assets/`
- OpenAI smoke artifact target: `docs/examples/openai_smoke_success.json`
- ACP validation notes: `docs/ACP_VALIDATION.md`
- Closeout checklist: `docs/CLOSEOUT_CHECKLIST.md`
- Flow-by-flow validation log: `docs/VALIDATION_MATRIX.md`
- Delivery status summary: `docs/DELIVERY_STATUS.md`
- Manual closeout runbook: `docs/MANUAL_CLOSEOUT_PACK.md`

## Packaging checklist

- LICENSE present
- README includes setup, CLI usage, ACP usage, demo path, and limitations
- Team information documented
- CLI fallback documented
- Automated and repo-local validation recorded in `docs/VALIDATION_MATRIX.md`
- Repo visibility must be confirmed manually before submission
- Video link and screenshot filenames must be filled in before submission
