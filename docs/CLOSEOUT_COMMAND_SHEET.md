# Closeout Command Sheet

Use this file for the final delivery pass. Run the sections in order and update the linked docs as each gate closes.

## 0. Preflight

From the repo root:

```bash
pwd
make test
make demo-smoke
make verify-crosshair
make verify-acp
```

Expected:

- `make test` passes
- `make demo-smoke` shows the planted failing test first, then a `VERIFIED` ledger
- `make verify-crosshair` shows one verified case and one falsified witness
- `make verify-acp` prints `Axiom ACP agent import ok`

If any of those fail, stop and fix that issue before doing screenshots or rehearsal.

## 1. ACP Validation

Target doc:

- [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1)

Open JetBrains with AI Assistant enabled, load this repo, and register the agent from:

- [acp.json](/Users/alhinai/Desktop/TRUE/acp.json:1)

### ACP prompt 1: path-driven

Replace `/absolute/path/to/...` with the real repo path:

```text
bug=/absolute/path/to/demo_repo/checkout/discount.py
test=/absolute/path/to/demo_repo/tests/test_discount.py
```

Expected:

- Axiom appears in the agent picker
- Axiom can be selected
- The returned message is a full Evidence Ledger
- Final status is `VERIFIED`

### ACP prompt 2: pasted-text

````text
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

```text
Traceback (most recent call last):
AssertionError: discount should not go negative for pct > 100
```
````

Expected:

- The prompt is accepted without path syntax
- Axiom returns a readable Evidence Ledger
- The prompt does not crash or fall back to generic guidance

### ACP screenshots to capture

- agent picker
- selected `Axiom` agent
- successful returned ledger

Save the ACP screenshot as one of:

- `docs/assets/09_acp_success.png`
- `docs/assets/09_acp_attempt.png` if ACP fails but the failure is documented honestly

### ACP record fields to fill in

Update [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1):

- IDE version
- AI Assistant version
- Date validated
- Screenshot filenames
- Quirks / workarounds

## 2. Screenshot Capture

Asset index:

- [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1)

Rules:

- no secrets visible
- no API keys visible
- crop noise
- keep terminal and ledger text readable
- use the exact filenames from the asset README

### Screenshot commands

Failing test before patch:

```bash
PYTHONPATH=src ./.venv/bin/python -m pytest demo_repo/tests/test_discount.py -q
```

Capture as:

- `docs/assets/01_failing_test.png`

Verified CLI result:

```bash
make demo
```

Capture as:

- `docs/assets/02_demo_verified.png`

Falsified CLI result:

```bash
make demo-falsified
```

Capture as:

- `docs/assets/03_demo_falsified.png`

Unproven CLI result:

```bash
make demo-unproven
```

Capture as:

- `docs/assets/04_demo_unproven.png`

Stacktrace + function happy path:

```bash
tmpdir=$(mktemp -d)
printf 'Traceback (most recent call last):\nAssertionError: negative result\n' > "$tmpdir/stacktrace.txt"
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --stacktrace "$tmpdir/stacktrace.txt" \
  --function demo_repo/checkout/discount.py
```

Capture as:

- `docs/assets/05_cli_stacktrace_function.png`

Bug report + function happy path:

```bash
tmpdir=$(mktemp -d)
printf 'apply_discount should reject percentages above 100 because the result can become negative.\n' > "$tmpdir/bug_report.txt"
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --bug-report "$tmpdir/bug_report.txt" \
  --function demo_repo/checkout/discount.py
```

Capture as:

- `docs/assets/06_cli_bugreport_function.png`

Codex workflow validation:

```bash
codex exec -C /Users/alhinai/Desktop/TRUE --skip-git-repo-check "Reply with exactly: codex-ok"
```

Capture as:

- `docs/assets/07_codex_smoke.png`

Direct OpenAI API validation, only with a fresh valid key:

```bash
OPENAI_API_KEY='<fresh-valid-key>' OPENAI_MODEL='gpt-5.4' \
  PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py
```

Capture as:

- `docs/assets/08_openai_smoke_success.png`

Optional clean failure mode:

```bash
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --stacktrace missing.txt \
  --function demo_repo/checkout/discount.py
```

Capture as:

- `docs/assets/10_cli_failure_mode.png`

Optional Non-Contradiction demo:

```bash
make demo-non-contradiction
```

Capture as:

- `docs/assets/11_demo_non_contradiction.png`

Expected:

- `Axiom:          Non-Contradiction`
- `Verification:   VERIFIED`

Optional Identity demo:

```bash
make demo-identity
```

Capture as:

- `docs/assets/12_demo_identity.png`

Expected:

- `Axiom:          Identity`
- `Verification:   VERIFIED`

## 3. Backup Video

Record one 60-second CLI-only fallback demo and save it as:

- `docs/assets/backup_demo_60s.mp4`

Suggested order:

1. show failing test
2. run `make demo`
3. show `VERIFIED`
4. run `make demo-falsified`
5. show witness
6. run `make demo-unproven`
7. end on the honest ledger framing

Optional follow-up commands, only if the main path is already clean:

```bash
make demo-non-contradiction
make demo-identity
```

## 4. Rehearsal

Checklist target:

- [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1)

Run the final sequence three times:

1. `make demo`
2. `make demo-falsified`
3. `make demo-unproven`

If the live plan includes ACP, rehearse one ACP run too.

Log under:

- `Rehearsal 1`
- `Rehearsal 2`
- `Rehearsal 3`

Recommended note format:

- date/time
- ran ACP or CLI
- anything surprising
- whether the sequence was clean

## 5. Final Closeout

Update these files after validation:

- [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1)
- [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1)
- [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1)
- [docs/DELIVERY_STATUS.md](/Users/alhinai/Desktop/TRUE/docs/DELIVERY_STATUS.md:1)

Final sign-off fields:

- Closeout status: `READY`
- Final reviewer
- Date
- Notes

Then do one final sanity pass:

```bash
make test
make demo-smoke
make verify-crosshair
make verify-acp
```

If those are green and the manual items are filled in, move the project from `NEAR-READY` to `READY`.
