# Validation Matrix

This file records the actual validation passes that were completed from the repo workspace, plus the external/manual checks that still require live confirmation.

## Automated and repo-local validation

| Flow | Command / input | Expected behavior | Actual behavior | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Full test suite | `make test` | All tests pass | `42 passed in 7.78s` | Pass | Includes CLI, parser, agent routing, pipeline, verifier, ledger, multi-function targeting, original-source verification, retry coverage, and optional axiom demo coverage |
| ACP import smoke | `make verify-acp` | Agent imports cleanly | `Axiom ACP agent import ok` | Pass | Does not prove JetBrains IDE integration |
| CrossHair smoke | `make verify-crosshair` | Verified case passes, falsified case yields witness | Verified case passed; falsified case returned `apply_discount(0.5, 101)` witness | Pass | Meets repo-local verifier gate |
| Codex workflow smoke | `codex exec -C /Users/alhinai/Desktop/TRUE --skip-git-repo-check "Reply with exactly: codex-ok"` | Codex CLI runs non-interactively in this workspace | Returned `codex-ok` | Pass | Proves Codex-authenticated terminal workflow, not direct API-key validation |
| Direct OpenAI API smoke | `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py` | Structured-output smoke succeeds and writes validation artifact | Passed and wrote `docs/examples/openai_smoke_success.json` | Pass | Auth mode: `OPENAI_API_KEY`; repo default model: `gpt-5.4` |

## CLI happy-path flows

| Flow | Command / input | Expected behavior | Actual behavior | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Bug + test | `make demo` | Produce readable `VERIFIED` ledger | Returned `VERIFIED`, `1/1 passing` | Pass | Primary demo path |
| Original bug witness | `make demo-falsified` | Produce readable `FALSIFIED` ledger with counterexample | Returned `FALSIFIED` with `apply_discount(0.5, 101)` | Pass | Good dramatic witness path |
| Forced unproven | `make demo-unproven` | Produce readable `UNPROVEN` ledger | Returned `UNPROVEN` with timeout messaging | Pass | Honest fallback path |
| Non-Contradiction bug + test | `make demo-non-contradiction` | Produce readable `VERIFIED` ledger for contradictory state bug | Returned `VERIFIED`, `1/1 passing` | Pass | Optional second bug flow |
| Identity bug + test | `make demo-identity` | Produce readable `VERIFIED` ledger for identifier-mixup bug | Returned `VERIFIED`, `1/1 passing` | Pass | Optional third bug flow |
| Stacktrace + function | `axiom-cli --stacktrace <file> --function demo_repo/checkout/discount.py` | Produce valid ledger | Returned `VERIFIED` ledger | Pass | Runs without pytest because no test file is supplied |
| Bug report + function | `axiom-cli --bug-report <file> --function demo_repo/checkout/discount.py` | Produce valid ledger | Returned `VERIFIED` ledger | Pass | Good fallback when only natural-language context exists |

## Prompt parser flows

| Flow | Source | Expected behavior | Actual behavior | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Pasted function + failing test | `tests/test_agent_parsing.py` | Identify function block and test/error block | Parser returns actionable request | Pass | Covered by unit test |
| Pasted function + stacktrace | `tests/test_agent_parsing.py` | Identify function block and stacktrace | Parser returns actionable request | Pass | Covered by unit test |
| Pasted async function + stacktrace | `tests/test_agent_parsing.py` | Identify async function blocks too | Parser returns actionable request | Pass | Guards ACP async-function parsing |
| Bug report + function | `tests/test_agent_parsing.py` | Identify natural-language context and function | Parser returns actionable request | Pass | Covered by unit test |
| Bug report mentioning a test name | `tests/test_agent_parsing.py` | Stay in bug-report mode instead of misclassifying as test input | Parser keeps `context` and omits `error_info` | Pass | Prevents `test_...` prose from flipping routes |
| Path-driven fallback | `tests/test_agent_parsing.py` | Preserve `bug=/...` fallback | Parser returns path-mode request | Pass | Keeps ACP fallback available |
| Path mode `function + stacktrace` | `tests/test_agent_parsing.py` | Load both files and preserve actionable request | Parser returns actionable request | Pass | Covers ACP file-based stacktrace flow |
| Path mode ambiguity rejection | `tests/test_agent_parsing.py` | Reject contradictory combinations instead of silently picking one | Raises `ValueError` | Pass | Keeps ACP path mode aligned with CLI semantics |
| Path mode empty-file rejection | `tests/test_agent_parsing.py` | Empty stacktrace file fails clearly | Raises `ValueError` | Pass | Matches CLI empty-file safeguards |
| Malformed prompt | `tests/test_agent_parsing.py` | Return guidance, not crash | Parser returns non-actionable result; guidance text available | Pass | Guidance message is stable |

## Agent routing flows

| Flow | Source | Expected behavior | Actual behavior | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Pasted failing test routed through ACP agent | `tests/test_agent.py` | Build actionable pipeline input and pass test body as analysis context | Agent routes request and preserves failing-test text | Pass | Confirms ACP behavior beyond parser-only tests |
| Ambiguous ACP path mode | `tests/test_agent.py` | Return precise error plus guidance | Agent returns validation error message | Pass | Prevents silent branch selection |
| ACP path mode `function + stacktrace` | `tests/test_agent_parsing.py` + `tests/test_agent.py` | Accept file-backed stacktrace routing cleanly | Parser and agent coverage both present | Pass | Verifies ACP path-mode stacktrace flow from parse through route selection |
| ACP path mode empty-file rejection | `tests/test_agent_parsing.py` | Reject empty stacktrace inputs with a precise validation error | Raises `ValueError` | Pass | Aligns ACP path mode with CLI safeguards |

## Failure modes

| Flow | Command / input | Expected behavior | Actual behavior | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Missing stacktrace file | `axiom-cli --stacktrace missing.txt --function demo_repo/checkout/discount.py` | Clear error, nonzero exit | `Stacktrace file not found: missing.txt` | Pass | Exit code `2` |
| Empty stacktrace file | `axiom-cli --stacktrace <empty> --function demo_repo/checkout/discount.py` | Clear error, nonzero exit | `Stacktrace file is empty: ...` | Pass | Exit code `2` |
| Invalid flag combination | `axiom-cli --stacktrace stack.txt --function ... --test ...` | Helpful error, nonzero exit | `` `--test` is only supported with `--bug` mode. `` | Pass | Exit code `2` |
| No OpenAI key | `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py` | Loud failure, nonzero exit | `OPENAI_API_KEY is not set; live OpenAI validation cannot run.` | Pass | Expected repo-local failure mode until key is available |

## External/manual validation still required

| Flow | Required evidence | Current status | Notes |
| --- | --- | --- | --- |
| JetBrains ACP end-to-end run | IDE screenshots + reproduction notes | Pending | See [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1) |
| Screenshots and backup video | Files in `docs/assets/` | Pending | See [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1) |
| Rehearsal | Notes and sign-off | Pending | Record outcome in [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1) |
