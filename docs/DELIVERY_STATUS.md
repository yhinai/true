# Delivery Status

I’ve now locked the validation matrix using real command evidence and converted that into repo artifacts. The current pass adds a flow-by-flow validation log, splits the closeout checklist by completion state, and tightens the demo/checklist scripts so they match the current product surface exactly.

## What was added

`docs/VALIDATION_MATRIX.md` now captures real command results for:

- `make test`
- `make verify-acp`
- `make verify-crosshair`
- `make demo`
- `make demo-falsified`
- `make demo-unproven`
- `--stacktrace + --function`
- `--bug-report + --function`
- key failure modes

`docs/CLOSEOUT_CHECKLIST.md` is now split into:

- completed repo-local work
- pending manual/external validation
- current blockers
- rehearsal log and final sign-off

`docs/SUBMISSION.md` now references the validation log as part of the delivery story.

`scripts/record_demo_checklist.sh` now matches the shipped demo commands and fallback path.

## What was re-verified

- `make test` -> passes (`42 passed`)
- `make verify-acp` -> passes import smoke
- `make verify-crosshair` -> verified case passes and falsified case yields a witness
- `codex exec -C /Users/alhinai/Desktop/TRUE --skip-git-repo-check "Reply with exactly: codex-ok"` -> Codex-authenticated workflow passes in this shell
- `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py` -> direct OpenAI API validation passes and writes `docs/examples/openai_smoke_success.json`
- `make demo` -> `VERIFIED`
- `make demo-falsified` -> `FALSIFIED` with `apply_discount(0.5, 101)`
- `make demo-unproven` -> `UNPROVEN`
- `make demo-non-contradiction` -> `VERIFIED`
- `make demo-identity` -> `VERIFIED`
- `axiom-cli --stacktrace ... --function ...` -> valid ledger
- `axiom-cli --bug-report ... --function ...` -> valid ledger
- expected CLI failure modes still fail clearly
- `scripts/smoke_openai.py` still fails loudly without `OPENAI_API_KEY`
- multi-function target selection now follows the function named in bug context instead of blindly taking the first `def`
- `--verify-original` now skips patch generation entirely, so the falsified witness path stays offline-safe
- pipeline retries now match the plan: first attempt plus up to two counterexample-guided retries
- contracts now attach to the classified target function instead of the first function in the file
- CrossHair now targets the selected function line instead of checking the entire temp file indiscriminately
- pytest counts in the Evidence Ledger now reflect the actual test summary instead of a hardcoded `1/0`
- ACP path mode now rejects ambiguous combinations and empty files with clear validation errors
- optional Non-Contradiction and Identity demo fixtures are now implemented, documented, and locally smoke-tested
- ACP path-mode validation now has both parser-level and agent-routing coverage in the repo test suite

## Current demo flow

1. Show the failing discount test.
2. Run `make demo`.
3. Show the `VERIFIED` ledger.
4. Run `make demo-falsified` and show the concrete CrossHair witness.
5. Run `make demo-unproven` to show the honest `UNPROVEN` path.
6. If ACP fails live, switch immediately to the CLI and keep the ledger surface the same.

## What remains and still cannot be closed from repo-only execution

- JetBrains ACP end-to-end validation in the IDE
- Screenshots and 60-second backup video
- Rehearsal and final freeze/sign-off

At this point, the repo is in a stronger `NEAR-READY` state: Codex workflow validation and direct OpenAI API validation are both complete, and the remaining open items are the manual/external ones called out in [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1).

## Recommended next actions

1. Run the IDE flow from [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1) and capture screenshots.
2. Capture the assets listed in [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1).
3. Fill in rehearsal and sign-off in [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1).

This note can also be adapted into a shorter Slack update or a more formal delivery-status summary.
