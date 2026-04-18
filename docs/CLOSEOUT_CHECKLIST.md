# Closeout Checklist

Status target: DELIVERY VALIDATION COMPLETE

## Completed repo-local items

| Acceptance item | Owner | Status | Proof |
| --- | --- | --- | --- |
| Repo tests are green | P1 + P2 + P3 | Complete | `make test`, [docs/VALIDATION_MATRIX.md](/Users/alhinai/Desktop/TRUE/docs/VALIDATION_MATRIX.md:1) |
| CLI supports both planned input modes | P1 | Complete | [src/axiom/cli.py](/Users/alhinai/Desktop/TRUE/src/axiom/cli.py:1), [tests/test_cli.py](/Users/alhinai/Desktop/TRUE/tests/test_cli.py:1) |
| ACP prompt parsing handles pasted bug context | P1 + P2 | Complete in repo | [src/axiom/prompt_parser.py](/Users/alhinai/Desktop/TRUE/src/axiom/prompt_parser.py:1), [tests/test_agent_parsing.py](/Users/alhinai/Desktop/TRUE/tests/test_agent_parsing.py:1) |
| CLI modes are verified end-to-end | P1 | Complete in repo | [docs/VALIDATION_MATRIX.md](/Users/alhinai/Desktop/TRUE/docs/VALIDATION_MATRIX.md:1) |
| Codex-authenticated workflow validation passes | P2 | Complete in current shell | [docs/OPENAI_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/OPENAI_VALIDATION.md:1) |
| Direct OpenAI API smoke passes with a real API key and structured output | P2 | Complete in current shell | [docs/OPENAI_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/OPENAI_VALIDATION.md:1), [docs/examples/openai_smoke_success.json](/Users/alhinai/Desktop/TRUE/docs/examples/openai_smoke_success.json:1) |
| Submission packaging baseline exists | P4 | Complete in repo | [README.md](/Users/alhinai/Desktop/TRUE/README.md:1), [docs/SUBMISSION.md](/Users/alhinai/Desktop/TRUE/docs/SUBMISSION.md:1), [LICENSE](/Users/alhinai/Desktop/TRUE/LICENSE:1), [docs/TEAM.md](/Users/alhinai/Desktop/TRUE/docs/TEAM.md:1) |

## Pending manual / external validation

| Acceptance item | Owner | Status | Proof / next action |
| --- | --- | --- | --- |
| ACP validated end-to-end in JetBrains AI Chat | P1 | Pending | Run the IDE flow in [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1) using [docs/CLOSEOUT_COMMAND_SHEET.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_COMMAND_SHEET.md:1) |
| Backup demo assets exist | P4 | Pending | Capture files listed in [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1) using [docs/CLOSEOUT_COMMAND_SHEET.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_COMMAND_SHEET.md:1) |
| README / submission docs exactly match shipped behavior after external validation | P4 | Pending final doc pass | Update screenshots, IDE notes, and OpenAI results after manual validation |
| Golden-path demo rehearsed 3 times without surprises | All | Pending | Record rehearsal notes and sign-off below using [docs/CLOSEOUT_COMMAND_SHEET.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_COMMAND_SHEET.md:1) |
| Delivery artifact frozen and ready for handoff | Team lead | Pending | Final freeze only after the manual items above are complete |

## Current blockers

- JetBrains IDE access and one witnessed ACP run are still required.
- Screenshots and backup video have not been captured yet.
- Rehearsal has not been logged yet.

## Rehearsal log

- Rehearsal 1:
  - Date/time:
  - Mode: `CLI / ACP`
  - Result: `Clean / Minor issue / Failed`
  - Notes:
- Rehearsal 2:
  - Date/time:
  - Mode: `CLI / ACP`
  - Result: `Clean / Minor issue / Failed`
  - Notes:
- Rehearsal 3:
  - Date/time:
  - Mode: `CLI / ACP`
  - Result: `Clean / Minor issue / Failed`
  - Notes:

## Final sign-off

- Closeout status: `READY / NEAR-READY / NOT READY`
- Final reviewer:
- Date:
- Notes:

## Minimal Reply To Send Back

If you want me to fill this checklist in after the manual run, send:

```text
ACP validated in JetBrains: Yes/No
Assets captured: Yes/No
README/submission docs need final edits: Yes/No

Rehearsal 1:
- date/time:
- mode:
- result:
- notes:

Rehearsal 2:
- date/time:
- mode:
- result:
- notes:

Rehearsal 3:
- date/time:
- mode:
- result:
- notes:

Final sign-off:
- status:
- reviewer:
- date:
- notes:
```

## Freeze Rule

- No new features
- No second bug work
- No ACP registry work before JetBrains validation
- No polish work ahead of validation blockers
