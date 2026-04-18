# OpenAI and Codex Validation

## Validation tracks

This repo now treats Codex workflow validation and direct OpenAI API validation as two separate checks because they prove different things.

### Track 1: Codex-authenticated workflow validation

Goal:

- Prove that the Codex CLI is installed and authenticated in the current terminal.
- Prove that a Codex-assisted repo workflow can run non-interactively from this workspace.

Command used in the latest validation pass:

```bash
codex exec -C /Users/alhinai/Desktop/TRUE --skip-git-repo-check "Reply with exactly: codex-ok"
```

Observed result:

- `codex` is installed at `/Users/alhinai/.nvm/versions/node/v24.14.1/bin/codex`
- non-interactive execution started successfully
- provider reported by Codex: `openai`
- model reported by Codex: `gpt-5.4`
- final output included the requested `codex-ok`

Success criteria:

- `codex` command exists
- `codex exec` runs without auth failure
- one non-interactive command completes successfully in this repo

Status:

- Completed in the current shell

### Track 2: Direct OpenAI API validation

Goal:

- Prove that live structured output works with a real `OPENAI_API_KEY` in this environment.
- Prove that the repo-default API model can return parseable structured output for both classification and patch generation.

Command:

```bash
PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py
```

Success criteria:

- `OPENAI_API_KEY` is present
- Bug classification parses into `BugClassification`
- Patch generation parses into `PatchProposal`
- Success artifact is written to `docs/examples/openai_smoke_success.json`

## Model

- Codex workflow validation observed `gpt-5.4`
- API smoke default: `gpt-5.4`
- API smoke can override with `OPENAI_MODEL`

## Current status

- Codex-authenticated workflow validation passed in the current shell
- Repo-side API smoke script is implemented
- Direct API validation completed successfully on 2026-04-18
- Command used: `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py`
- Auth mode: `OPENAI_API_KEY`
- Result: passed
- Artifact: `docs/examples/openai_smoke_success.json`
- Structured output parsed cleanly into `BugClassification` and `PatchProposal`

## Minimal Reply To Send Back

If you rerun the live API smoke and want me to refresh this file, send:

```text
Date:
Command:
Model:
Auth mode:
Result: Passed/Failed
Artifact updated: Yes/No
Notes:
```
