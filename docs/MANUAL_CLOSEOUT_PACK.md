# Manual Closeout Pack

Final steps to go from `NEAR-READY` to `READY`.

## Current honest state

The repo is `NEAR-READY`.

Already complete:

- repo tests pass
- CrossHair flows pass
- CLI flows are validated
- Codex workflow is validated
- direct OpenAI API smoke is validated
- validation/docs for those tracks are in place

Still open:

- JetBrains ACP end-to-end validation in the real IDE
- screenshots and 60-second backup video
- rehearsal log
- final freeze / sign-off

The remaining work is purely manual/external.

## Part 1 - Exact ACP closeout run

### Goal

Produce one real, reproducible JetBrains ACP success and record it.

### What to prepare

- JetBrains IDE open on the repo
- ACP configured as described in [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1)
- one known-good demo target ready
- terminal available in case fallback to CLI is needed
- screenshot tool ready

### Recommended ACP validation scenario

Use the simplest supported happy path that matches the shipped surface.

Preferred scenario:

- use the discount demo / known verification path
- ask ACP to analyze the bug / verification case
- confirm it produces the expected ledger/result surface

### Minimum evidence required

1. ACP is visible in the IDE
2. repo/project is visible
3. prompt or invocation is visible
4. successful result is visible
5. result is consistent with the expected product surface

### ACP run checklist

- [ ] Open project in JetBrains
- [ ] Confirm ACP plugin/integration is enabled
- [ ] Confirm repo indexes/load are complete
- [ ] Start one supported end-to-end flow
- [ ] Wait for result
- [ ] Confirm output is a valid expected result
- [ ] Capture screenshots
- [ ] Record exact notes in `docs/ACP_VALIDATION.md`

### What to record in `docs/ACP_VALIDATION.md`

1. Environment

- IDE name + version
- OS
- ACP/plugin version if visible
- repo commit / branch if relevant

2. Scenario run

- what prompt / action was used
- what file/context was open
- what expected behavior was

3. Observed result

- success / fail
- summary of returned output
- whether ledger surface matched CLI expectations

4. Evidence

- screenshot filenames
- any caveats

Suggested wording:

JetBrains ACP end-to-end validation was completed in the IDE on a real project checkout. A supported flow was executed successfully, and the resulting output matched the expected ledger/result surface. Screenshots were captured in `docs/assets/` and the reproduction notes below reflect the actual run conditions.

If ACP fails, do not fake success. Record it honestly:

JetBrains ACP end-to-end validation was attempted but did not complete successfully in the IDE environment. The project remains demoable via the validated CLI fallback path, which preserves the same ledger/result surface. Failure details and environment notes are recorded below.

## Part 2 - Exact screenshot list

### Goal

Capture only what is needed, with filenames that match the docs.

### Required screenshots

1. `01_failing_test.png`
   show the failing discount test or initial problem state

2. `02_demo_verified.png`
   show `make demo` producing `VERIFIED`

3. `03_demo_falsified.png`
   show `make demo-falsified` producing `FALSIFIED`
   include the concrete witness/counterexample if visible

4. `04_demo_unproven.png`
   show `make demo-unproven` producing `UNPROVEN`

5. `05_cli_stacktrace_function.png`
   show `axiom-cli --stacktrace ... --function ...`
   include valid ledger output

6. `06_cli_bugreport_function.png`
   show `axiom-cli --bug-report ... --function ...`
   include valid ledger output

7. `07_codex_smoke.png`
   show the successful Codex workflow smoke command/result

8. `08_openai_smoke_success.png`
   show the successful real OpenAI smoke validation

9. `09_acp_success.png`
   show the successful JetBrains ACP IDE run

If ACP fails, replace with:

- `09_acp_attempt.png`

Optional:

10. `10_cli_failure_mode.png`
    show one cleanly handled invalid input / failure case

### Screenshot rules

- no secrets visible
- no API keys visible
- zoom enough to read the important output
- crop out noise
- keep terminal font large enough
- do not include unrelated windows/tabs

### What to update after capture

In [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1), list each screenshot with one line of explanation.

## Part 3 - 60-second backup video

### Goal

Create one short backup demo that tells the whole story if a live demo goes sideways.

### Video structure

0-8 sec

- show repo/project name
- one sentence: what the tool does

8-18 sec

- show failing input/test

18-30 sec

- run or show `make demo`
- show `VERIFIED`

30-40 sec

- show `make demo-falsified`
- point to the witness/counterexample

40-48 sec

- show `make demo-unproven`
- point to honest `UNPROVEN` outcome

48-56 sec

- briefly show Codex / ACP / OpenAI validation evidence

56-60 sec

- close with “repo validated; remaining delivery evidence captured here”

### Video rules

- no long typing
- no secrets
- no dead time
- keep cursor movement minimal
- use prepared windows/commands
- prefer cuts over scrolling

Recommended filename:

- `backup_demo_60s.mp4`

Update [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1) after recording.

## Part 4 - Exact rehearsal checklist

### Goal

Log a real rehearsal, not just intent.

### Technical rehearsal checklist

- [ ] terminal is clean
- [ ] repo is at final intended commit
- [ ] demo commands are pre-copied
- [ ] required files are in place
- [ ] ACP window is ready if used
- [ ] fallback CLI window is ready
- [ ] screenshots/video are accessible
- [ ] no secrets visible
- [ ] commands run in expected order
- [ ] results appear as expected

### Narrative rehearsal checklist

- [ ] can explain the project in 1-2 sentences
- [ ] can explain supported flows
- [ ] can explain `VERIFIED` / `FALSIFIED` / `UNPROVEN` clearly
- [ ] can explain Codex vs OpenAI API validation
- [ ] can explain ACP vs CLI fallback
- [ ] can explain what is complete vs what was manual

### Failure-mode rehearsal checklist

- [ ] practiced ACP failure fallback to CLI
- [ ] practiced not relying on live OpenAI during demo
- [ ] practiced using screenshots/video if needed
- [ ] practiced finishing the demo without improvising

### What to write in `docs/CLOSEOUT_CHECKLIST.md`

Use this template:

Rehearsal log

- Date:
- Environment:
- Rehearsal type: technical / narrative / fallback
- Result: PASS / PASS WITH NOTES / FAIL
- Notes:

Example:

- Date: 2026-04-18
- Environment: local terminal + JetBrains IDE
- Rehearsal type: technical + fallback
- Result: PASS WITH NOTES
- Notes: live flow worked; ACP fallback to CLI was also tested successfully; minor terminal resizing cleaned up before final demo.

## Part 5 - Final freeze / sign-off

### Goal

Move the repo from `NEAR-READY` to `READY` honestly.

### Freeze checklist

- [ ] no more feature changes
- [ ] no pending doc mismatches
- [ ] all screenshots present
- [ ] backup video present
- [ ] ACP result recorded
- [ ] OpenAI result recorded
- [ ] validation matrix final
- [ ] closeout checklist final
- [ ] delivery status final
- [ ] final demo commands frozen

### What to write in `docs/CLOSEOUT_CHECKLIST.md`

Final sign-off

- Date:
- Signed off by:
- Repo state:
- Status: READY / NEAR-READY / NOT READY
- Notes:

Suggested `READY` wording:

- Date: 2026-04-18
- Signed off by: <name>
- Repo state: delivery candidate frozen
- Status: READY
- Notes: repo-local validation, Codex workflow validation, direct OpenAI API validation, JetBrains ACP IDE validation, demo assets, and rehearsal have all been completed. The delivery surface is frozen and ready for handoff.

Suggested `NEAR-READY` wording:

- Date: 2026-04-18
- Signed off by: <name>
- Repo state: delivery candidate not yet frozen
- Status: NEAR-READY
- Notes: core repo validation is complete, but one or more manual/external closeout items remain open. See blockers above.

## Part 6 - Exact doc updates after manual closeout

After ACP + assets + rehearsal are done, update these files:

1. [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1)
   Mark ACP validation complete and attach screenshot references.

2. [docs/assets/README.md](/Users/alhinai/Desktop/TRUE/docs/assets/README.md:1)
   List all real screenshots and the backup video.

3. [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1)
   Fill in:
   - ACP completion
   - screenshots/video completion
   - rehearsal log
   - final sign-off

4. [docs/DELIVERY_STATUS.md](/Users/alhinai/Desktop/TRUE/docs/DELIVERY_STATUS.md:1)
   Change status from `NEAR-READY` to `READY`.

Suggested final status wording:

The project is now READY. Repo-local behavior, CrossHair verification flows, CLI validation, Codex workflow validation, direct OpenAI API validation, and JetBrains ACP IDE validation are all complete. Demo assets have been captured, rehearsal has been logged, and the delivery surface is frozen for handoff.

5. [docs/SUBMISSION.md](/Users/alhinai/Desktop/TRUE/docs/SUBMISSION.md:1)
   Make sure it references:
   - validation matrix
   - ACP validation notes
   - assets list
   - final delivery status

## Part 7 - Fastest path to READY

Do these in this exact order:

1. Run the JetBrains ACP flow and capture:
   - `09_acp_success.png`

2. Capture any missing screenshots:
   - `01` through `08` if not already done

3. Record:
   - `backup_demo_60s.mp4`

4. Fill in rehearsal log in:
   - `docs/CLOSEOUT_CHECKLIST.md`

5. Fill in final sign-off in:
   - `docs/CLOSEOUT_CHECKLIST.md`

6. Update:
   - `docs/ACP_VALIDATION.md`
   - `docs/assets/README.md`
   - `docs/DELIVERY_STATUS.md`
   - `docs/SUBMISSION.md`

7. Re-read all four docs once for consistency

## Part 8 - Honest final decision rule

Mark the project `READY` only if all of these are true:

- ACP run really happened
- screenshots/video really exist
- rehearsal really happened
- sign-off is really filled in

If any one of those is missing, leave it `NEAR-READY`.

## Part 9 - Final paste-ready status note

Use this once the last manual steps are actually complete:

The remaining manual closeout steps are now complete. JetBrains ACP end-to-end validation was run and documented, demo screenshots and the backup video were captured, rehearsal was logged, and the final freeze/sign-off was recorded. At this point the project is READY: repo-local validation, Codex workflow validation, direct OpenAI API validation, IDE validation, assets, and closeout documentation are all in place.

If ACP fails and the honest version is needed, use:

The repo remains NEAR-READY. Repo-local validation, Codex workflow validation, and direct OpenAI API validation are complete, but JetBrains ACP end-to-end validation did not complete successfully in the IDE environment. The CLI fallback path remains validated and demoable, and all open manual blockers are recorded in the closeout checklist.
