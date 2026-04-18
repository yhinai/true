AXIOM — COMPLETE MASTER BUILD PLAN
JetBrains Codex Hackathon · Apr 18–19, 2026 · 4-person team
Track: Problem Statement Two — Testing & Debugging Code
Project: Axiom
Tagline: Codex generates. Axiom proves.
Core claim: Axiom proposes a patch, derives contracts, verifies them with CrossHair, and returns one of three honest outcomes:
  VERIFIED / FALSIFIED / UNPROVEN

======================================================================
0. FINAL PRODUCT DEFINITION
======================================================================

Build a JetBrains ACP agent with a CLI fallback that:
1. accepts one input:
   - failing pytest test, OR
   - Python stacktrace, OR
   - small natural-language bug report
2. identifies the target function and likely axiom violation
3. asks Codex for a minimal patch
4. derives icontract preconditions/postconditions
5. runs CrossHair verification
6. optionally runs pytest
7. returns an Evidence Ledger with:
   - bug summary
   - chosen axiom
   - patch
   - contracts
   - verification result
   - counterexample if falsified
   - tests result
   - wall time
   - final status

FINAL DEMO SURFACE:
- JetBrains AI Chat agent named "Axiom" via ACP
- same functionality available through CLI if ACP fails
- one polished golden-path demo bug
- optional second and third bugs only after the first one is fully stable

DO NOT BUILD:
- Kotlin plugin
- web dashboard
- multi-agent orchestration platform
- generic theorem prover
- repo-wide refactor engine
- multiple languages
- fancy registry/distribution before core demo works

======================================================================
1. NON-NEGOTIABLE SUCCESS CRITERIA
======================================================================

Axiom is considered hackathon-ready only if ALL of these are true:

[ ] Axiom appears in JetBrains AI Chat OR CLI fallback works perfectly
[ ] One planted Python bug is fixed end-to-end
[ ] Axiom shows one VERIFIED result
[ ] Axiom shows one FALSIFIED result with a concrete counterexample
[ ] Axiom shows one UNPROVEN result or timeout path honestly
[ ] The Evidence Ledger is readable and memorable
[ ] A 60-second backup demo video exists
[ ] Submission repo and README are clean and reproducible

If any item above is missing, do not add features. Finish these first.

======================================================================
2. TEAM STRUCTURE
======================================================================

P1 — ACP / IDE / Interface Owner
- owns ACP agent visibility inside JetBrains
- owns session handling and message routing
- owns rendering of the Evidence Ledger in AI Chat
- owns CLI/ACP output consistency

P2 — Codex / Patch Generation Owner
- owns structured prompt design
- owns bug classification prompt
- owns patch generation prompt
- owns retry-with-counterexample flow
- owns pydantic schemas and model validation

P3 — Verification Owner
- owns icontract template generation
- owns CrossHair invocation
- owns parser for verified/falsified/unproven
- owns timeout handling and verifier stability
- owns contract library per axiom
- this is the most technical role

P4 — Demo / Hardening / Submission Owner
- owns demo repo and planted bugs
- owns pytest failure setup
- owns README, pitch notes, screenshots, backup video
- owns demo script and final submission packaging

Cross-team rules:
- stand-up every 4 hours, 5 minutes max
- no direct commits to main
- every PR reviewed by one other person
- after feature freeze: only bug fixes, polish, rehearsal

======================================================================
3. STACK (LOCK THIS)
======================================================================

Language:
- Python 3.12+

IDE integration:
- ACP agent (Agent Client Protocol) for JetBrains AI Chat
- CLI fallback is mandatory

LLM:
- OpenAI model via API, with a Codex-authenticated terminal workflow validated separately
- pydantic-validated structured outputs

Contracts:
- icontract

Verification:
- CrossHair

Testing:
- pytest
- optional Hypothesis fallback only if CrossHair becomes too slow

Supporting:
- pydantic
- rich (optional for CLI pretty output)
- uv or venv for environment setup

======================================================================
4. AXIOM FRAMING (KEEP IT SIMPLE)
======================================================================

Use the Four Axioms framing for pitch and organization, but do not overbuild all four if time is short.

Axiom 1 — Totality
Meaning:
- function handles all allowed inputs
Typical contract shape:
- require input ranges
- ensure result stays in allowed output range
Primary bug class:
- missing bounds
- empty cases
- negative or NaN outputs

Axiom 2 — Non-Contradiction
Meaning:
- impossible states must not coexist
Typical contract shape:
- invariants on class or state transitions
Primary bug class:
- loading=True and error!=None
- mutually exclusive state flags

Axiom 3 — Identity
Meaning:
- different conceptual identities are not interchangeable
Typical contract shape:
- stronger type or require-based checks
Primary bug class:
- user_id/order_id mixups
- wrong typed identifiers

Axiom 4 — Referential Integrity
Meaning:
- supposedly pure logic should not secretly mutate or diverge unexpectedly
Typical contract shape:
- output stability or purity-style checks
Primary bug class:
- hidden mutation
- changing input state during computation

RULE:
- fully implement Totality first
- only add Non-Contradiction and Identity after Totality is stable
- Referential Integrity is a stretch goal / backup talking point if time is tight

======================================================================
5. DEMO BUG STRATEGY
======================================================================

Primary demo bug (mandatory):
Bug A — Totality violation

Example target:
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100

Failing behavior:
- pct > 100 can yield negative result
- possibly bad handling for invalid inputs

Target contracts:
- @icontract.require(lambda price: price >= 0)
- @icontract.require(lambda pct: 0 <= pct <= 100)
- @icontract.ensure(lambda result: result >= 0)

Why this bug is perfect:
- tiny function
- obvious counterexample
- easy to verify
- easy to fix
- great stage demo

Secondary bug (optional after Bug A works):
Bug B — Non-Contradiction violation in a state object

Tertiary bug (optional after Bug B works):
Bug C — Identity violation with mixed identifiers

DO NOT TRY TO DEMO ALL FOUR AXIOMS LIVE.
Live demo should center on Bug A.
Mention Bug B/C in Q&A only if stable.

======================================================================
6. DIRECTORY STRUCTURE
======================================================================

repo/
├── src/axiom/
│   ├── __init__.py
│   ├── agent.py
│   ├── cli.py
│   ├── schema.py
│   ├── detector.py
│   ├── patcher.py
│   ├── contracts.py
│   ├── verifier.py
│   ├── ledger.py
│   ├── pipeline.py
│   ├── utils.py
│   └── axioms/
│       ├── __init__.py
│       ├── totality.py
│       ├── non_contradiction.py
│       ├── identity.py
│       └── referential_integrity.py
├── demo_repo/
│   ├── checkout/
│   │   ├── __init__.py
│   │   ├── discount.py
│   │   ├── order.py
│   │   └── fulfillment.py
│   └── tests/
│       ├── test_discount.py
│       ├── test_order.py
│       └── test_fulfillment.py
├── tests/
│   ├── test_detector.py
│   ├── test_patcher.py
│   ├── test_contracts.py
│   ├── test_verifier.py
│   ├── test_pipeline.py
│   └── test_cli.py
├── scripts/
│   ├── smoke_openai.py
│   ├── smoke_crosshair.sh
│   ├── smoke_acp.sh
│   └── record_demo_checklist.sh
├── docs/
│   ├── PITCH.md
│   ├── DEMO_SCRIPT.md
│   ├── ARCHITECTURE.md
│   └── SUBMISSION.md
├── acp.json
├── Makefile
├── pyproject.toml
└── README.md

======================================================================
7. PHASE 0 — PREP / ENVIRONMENT
======================================================================

Goal:
Everyone can install and run the stack locally before building anything serious.

Tasks:
1. create repo
2. set up Python environment
3. install dependencies
4. verify OpenAI access
5. verify CrossHair works
6. verify JetBrains AI Chat exists and ACP can be attempted
7. create scaffold

Dependencies:
- agent-client-protocol SDK or equivalent ACP Python library
- openai
- pydantic
- icontract
- crosshair-tool
- pytest
- hypothesis (fallback)
- rich

Deliverables:
- pyproject.toml
- Makefile
- empty package layout
- OPENAI_API_KEY working
- CrossHair installed
- JetBrains ready

PHASE 0 TEST GATE:
Run all of the following before proceeding:
- python -c "import openai"
- python -c "import icontract"
- python -c "import crosshair"
- crosshair --help
- python scripts/smoke_openai.py
- make demo-smoke

Expected:
- all imports succeed
- OpenAI returns a small smoke-test response
- CrossHair CLI works
- project imports

If any fail:
STOP. Fix environment first.

======================================================================
8. PHASE 1 — KILL-RISK SPIKES (DO THESE FIRST)
======================================================================

Goal:
Validate the 3 things most likely to kill the project before writing lots of code.

----------------------------------------------------------------------
PHASE 1A — CrossHair Spike
----------------------------------------------------------------------

Owner:
P3

Task:
Create one very small verified function and one very small falsified function using icontract, then run CrossHair.

Verified example:
- should pass in <= 5 seconds

Falsified example:
- should produce a concrete counterexample in <= 5 seconds

Deliverable:
- scripts/smoke_crosshair.sh
- documented timing numbers
- sample output

PHASE 1A TEST GATE:
- verified case returns cleanly
- falsified case returns counterexample
- both under acceptable time budget

Decision:
IF CrossHair is too slow or unstable:
- simplify demo function
- simplify contracts
- reduce scope
- if still bad, fallback to Hypothesis-based testing and keep “Unproven” honest

----------------------------------------------------------------------
PHASE 1B — ACP Spike
----------------------------------------------------------------------

Owner:
P1

Task:
Get a minimal Axiom ACP agent to appear in JetBrains AI Chat and respond with a stub message.

Deliverable:
- src/axiom/agent.py minimal skeleton
- acp.json manifest
- documented steps to add agent in IDE

PHASE 1B TEST GATE:
- Axiom appears in agent picker
- Axiom can be selected
- Axiom returns a stub message without crashing

Decision:
IF ACP is not working after 90 minutes:
- keep ACP as stretch
- switch primary demo path to CLI
- do not let ACP block core pipeline

----------------------------------------------------------------------
PHASE 1C — Codex Structured Output Spike
----------------------------------------------------------------------

Owner:
P2

Task:
Use Codex to classify a bug into one axiom with pydantic schema validation.

Deliverable:
- scripts/smoke_openai.py
- src/axiom/schema.py with at least:
  - BugClassification
  - PatchProposal
  - ContractProposal

PHASE 1C TEST GATE:
- Codex returns parseable structured JSON
- classification for Bug A is reasonable
- validation errors are recoverable

Decision:
IF model output is unstable:
- tighten prompt
- lower scope
- make schemas smaller
- add one repair retry
- keep output minimal

END OF PHASE 1 DECISION:
Proceed only if:
- CrossHair spike passes
- Codex spike passes
- ACP spike passes OR CLI fallback is clearly ready

======================================================================
9. PHASE 2 — DEMO REPO AND BUGS
======================================================================

Goal:
Create a tiny Python repo with planted bugs and failing tests.

Owner:
P4

Tasks:
1. create demo_repo/checkout/discount.py with Bug A
2. create demo_repo/tests/test_discount.py with a failing pytest case
3. optionally scaffold Bug B and Bug C, but do not prioritize them over Bug A
4. make test failure obvious and reproducible

Deliverables:
- reproducible failing test
- simple README note on what the bug is
- one command to run the failing test

PHASE 2 TEST GATE:
- pytest demo_repo/tests/test_discount.py fails reliably
- failure message is understandable
- bug is small enough for Codex to patch

If this test is flaky or ambiguous:
- simplify immediately
- remove any unnecessary complexity
- keep only one clean failing case

======================================================================
10. PHASE 3 — CORE MODULES
======================================================================

Goal:
Build the minimum viable internal engine.

----------------------------------------------------------------------
PHASE 3A — Schemas
----------------------------------------------------------------------

Owner:
P2

Implement:
- BugClassification
- PatchProposal
- ContractProposal
- VerificationOutcome
- EvidenceLedgerModel

Test:
- unit tests for schema validation
- malformed JSON rejected
- valid JSON parses cleanly

Milestone gate:
- pytest tests/test_schema.py passes

----------------------------------------------------------------------
PHASE 3B — Detector
----------------------------------------------------------------------

Owner:
P2

Implement:
- detector.py
- input:
  - failing test text
  - stacktrace
  - target function source
- output:
  - chosen axiom
  - confidence
  - short rationale
  - target function name

Test:
- Bug A classified as Totality
- output is stable over repeated runs
- confidence is numeric and bounded

Milestone gate:
- pytest tests/test_detector.py passes

----------------------------------------------------------------------
PHASE 3C — Patcher
----------------------------------------------------------------------

Owner:
P2

Implement:
- patcher.py
- generate minimal patch only
- keep same function signature
- return raw code or structured patch proposal
- support retry using counterexample feedback

Test:
- given Bug A source + failing test, returns a plausible fixed function
- patch is syntactically valid Python
- patch changes minimal relevant lines

Milestone gate:
- pytest tests/test_patcher.py passes

----------------------------------------------------------------------
PHASE 3D — Contracts
----------------------------------------------------------------------

Owner:
P3

Implement:
- contracts.py
- axioms/totality.py first
- function to derive icontract decorators from:
  - bug classification
  - target function source
  - optional Codex suggestions

Rules:
- keep contracts simple
- prefer verifiable contracts
- do not generate extremely complex lambdas
- start with require/ensure only

Test:
- contracts are syntactically valid
- contracts can be inserted above function
- contracts for Bug A reflect:
  - bounded pct
  - non-negative result

Milestone gate:
- pytest tests/test_contracts.py passes

----------------------------------------------------------------------
PHASE 3E — Verifier
----------------------------------------------------------------------

Owner:
P3

Implement:
- verifier.py
- write temp file with icontract and target function
- run CrossHair via subprocess
- parse output into:
  - VERIFIED
  - FALSIFIED
  - UNPROVEN
- extract counterexample if present
- enforce timeout

Test:
- verified example produces VERIFIED
- buggy example produces FALSIFIED
- timeout path produces UNPROVEN
- parser is stable

Milestone gate:
- pytest tests/test_verifier.py passes

----------------------------------------------------------------------
PHASE 3F — Ledger
----------------------------------------------------------------------

Owner:
P1 + P3

Implement:
- ledger.py
- render a compact human-readable Evidence Ledger
- must display:
  - bug
  - axiom
  - patch summary
  - contracts
  - verification result
  - counterexample if present
  - tests result
  - wall time
  - final status

Status values:
- VERIFIED
- FALSIFIED
- UNPROVEN

Test:
- snapshot-test formatted output
- verified case looks clean
- falsified case includes counterexample
- unproven case looks honest

Milestone gate:
- pytest tests/test_ledger.py passes

======================================================================
11. PHASE 4 — END-TO-END PIPELINE
======================================================================

Goal:
Join detector, patcher, contract generation, verifier, and ledger.

Owner:
P2 + P3 + P1

Implement:
- pipeline.py
- full flow:
  1. read failing test / stacktrace / bug report
  2. classify axiom
  3. generate patch
  4. derive contracts
  5. verify
  6. if falsified and retries remain:
       rerun patcher with counterexample feedback
  7. run pytest on patched function if feasible
  8. emit Evidence Ledger

Retry policy:
- max 2 retries after first attempt
- do not loop forever
- on repeated failure, return FALSIFIED or UNPROVEN honestly

PHASE 4 TEST GATE:
- one command runs pipeline on Bug A
- pipeline reaches one valid final status
- no crashes
- retry path works at least once in testing
- pipeline can show both:
  - a verified run
  - a falsified run using intentionally bad patch or broken original

If pipeline is unstable:
- remove retries
- remove extra bugs
- prioritize one stable end-to-end path

======================================================================
12. PHASE 5 — CLI FALLBACK (MANDATORY)
======================================================================

Goal:
Ensure the product can always be demoed even if ACP is flaky.

Owner:
P1 + P4

Implement:
- cli.py
- usage:
  axiom-cli --bug path/to/file.py --test path/to/test.py
  or
  axiom-cli --stacktrace stacktrace.txt --function function.py

Expected CLI behavior:
- runs full pipeline
- prints Evidence Ledger
- exits nonzero on serious errors
- supports demo quickly from terminal

PHASE 5 TEST GATE:
- CLI works on Bug A
- CLI produces readable ledger
- CLI can be used as full demo backup

RULE:
CLI fallback is not optional.
The project is not safe without it.

======================================================================
13. PHASE 6 — ACP INTEGRATION
======================================================================

Goal:
Wrap the pipeline inside ACP and render results in JetBrains AI Chat.

Owner:
P1

Implement:
- agent.py full prompt handling
- map incoming user prompt to pipeline input
- return Evidence Ledger text
- keep output compact
- do not overbuild advanced ACP features unless core works

Minimum ACP feature set:
- initialize
- new session
- prompt handling
- plain text result
- maybe simple progress text if easy

PHASE 6 TEST GATE:
- Axiom can be selected in JetBrains
- user pastes bug context
- Axiom returns full Evidence Ledger
- no crash during one full demo run

If ACP rendering is ugly but functional:
- keep it
- do not spend hours polishing if core proof path is still unstable

======================================================================
14. PHASE 7 — OPTIONAL EXPANSION
======================================================================

Only start this phase after:
- Bug A works end-to-end
- ACP or CLI is stable
- backup video exists

Possible expansions:
1. Bug B — Non-Contradiction
2. Bug C — Identity
3. Hypothesis-assisted “tested” evidence
4. richer Evidence Ledger
5. ACP registry submission
6. screenshots and nicer branding

RULE:
Do not add features that threaten the golden path.

======================================================================
15. MILESTONE TIMELINE
======================================================================

SATURDAY

Hour 0–1
- environment green
- repo scaffolded
- branches created

Hour 1–2
- CrossHair spike
- ACP spike
- Codex structured output spike

Milestone M1:
- kill-risk spikes resolved

Hour 2–4
- demo repo with Bug A
- detector / patcher / contracts skeleton
- verifier baseline

Milestone M2:
- Bug A failing test reproduced
- contracts generated
- verifier classifies basic examples

Hour 4–7
- end-to-end pipeline on Bug A
- ledger rendering
- CLI fallback functional

Milestone M3:
- first full run from bug -> ledger

Hour 7–10
- stable verified path
- stable falsified path
- ACP hooked up if possible

Milestone M4:
- live golden path demoable

SATURDAY NIGHT
- polish core
- add optional second bug only if safe
- record backup video
- improve pitch and screenshots

SUNDAY MORNING

Hour 0–3
- rehearse demo 3x
- fix only critical bugs
- create README and submission assets

Milestone M5:
- submission-ready package

Before deadline
- submit early
- do not wait until the last minute

======================================================================
16. TESTING AND DEBUGGING RULES
======================================================================

At every phase:
- no new phase starts until the prior phase has a passing verification gate
- every module gets at least one unit test
- every milestone gets one end-to-end smoke test
- every demo-critical path gets manually rehearsed

Required commands to maintain:
- make install
- make test
- make demo-smoke
- make demo
- make verify-crosshair
- make verify-acp

Debugging policy:
- if a step fails, write the failure reason in a shared notes doc
- do not silently skip broken verification
- if CrossHair times out, explicitly classify as UNPROVEN
- if Codex output is malformed, repair prompt or shrink schema
- if ACP blocks progress, continue via CLI
- if demo bug is too complex, simplify the bug, not the verifier

======================================================================
17. EVIDENCE LEDGER SPEC
======================================================================

The final Evidence Ledger should resemble:

--------------------------------------------------
AXIOM — Evidence Ledger
--------------------------------------------------
Bug:            apply_discount returns negative
Axiom:          Totality
Function:       apply_discount(price: float, pct: int)

Patch:
  [+3 -1 lines]

Contracts:
  @icontract.require(lambda price: price >= 0)
  @icontract.require(lambda pct: 0 <= pct <= 100)
  @icontract.ensure(lambda result: result >= 0)

Verification:
  VERIFIED | FALSIFIED | UNPROVEN

If VERIFIED:
  CrossHair: explored N paths / no counterexamples
  Tests:     X/Y passing
  Status:    Verified under contracts

If FALSIFIED:
  Counterexample:
    apply_discount(price=100, pct=150)
  Violated:
    result >= 0
  Status:
    Patch rejected — counterexample found

If UNPROVEN:
  CrossHair:
    timed out at T seconds
  Tests:
    X/Y passing
  Status:
    Passed tests but unproven beyond them

Wall time:
  2.3s

--------------------------------------------------

This card is the product.
Protect it.

======================================================================
18. DEMO SCRIPT
======================================================================

Live demo order:

1. Show failing test in PyCharm
2. Open AI Chat and select Axiom
3. Paste function + failing test
4. Axiom classifies the bug as Totality
5. Axiom proposes patch
6. Axiom adds contracts
7. Axiom runs verification
8. Show VERIFIED ledger

Then do dramatic second beat:
9. intentionally show broken/original variant
10. Axiom returns FALSIFIED
11. display exact counterexample
12. say:
   "Not a guess — a witness."

If ACP fails live:
- switch instantly to CLI
- run same golden path
- do not apologize excessively
- keep pitch moving

======================================================================
19. SUBMISSION CHECKLIST
======================================================================

[ ] repo public
[ ] MIT or permissive license
[ ] README with setup + demo steps
[ ] 60-second demo video uploaded
[ ] screenshots of VERIFIED/FALSIFIED/UNPROVEN
[ ] clear description of Track 2 fit
[ ] team members listed
[ ] all work created during event
[ ] one reproducible command for demo
[ ] CLI fallback documented
[ ] pitch practiced

======================================================================
20. HARD CUT LINES
======================================================================

If time gets tight, cut in this order:

1. cut ACP polish
2. cut extra bugs
3. cut registry/distribution work
4. cut advanced retry logic
5. cut fancy branding
6. cut optional hypothesis/property extras

Never cut:
- Bug A
- patch generation
- contract generation
- verifier
- Evidence Ledger
- CLI fallback
- backup video

======================================================================
21. FINAL DECISION TREE
======================================================================

If CrossHair is fast enough:
- use CrossHair as primary verifier

If CrossHair is too slow but works somewhat:
- simplify contracts and demo repo

If CrossHair is unusable:
- fallback to Hypothesis-based test evidence
- keep VERIFIED wording out
- use TESTED / FALSIFIED / UNPROVEN instead

If ACP works:
- demo in JetBrains AI Chat

If ACP fails:
- demo CLI inside PyCharm terminal

If Codex patching is unstable:
- constrain prompts harder
- reduce bug complexity
- allow manually seeded patch for one backup demo path

If everything is working:
- do not add scope
- rehearse more

======================================================================
22. STOP SECOND-GUESSING RULE
======================================================================

The winning version is:

Axiom =
  one Python bug
  + one JetBrains-facing ACP agent
  + one CLI fallback
  + one Codex patcher
  + one icontract generator
  + one CrossHair verifier
  + one unforgettable Evidence Ledger

Build that.
Verify every phase before moving on.
Do not expand until the golden path is rock solid.



FOLLOW UP PLAN:


AXIOM — DELIVERY CLOSEOUT PLAN
Goal: move Axiom from “prototype complete” to “plan-complete and hackathon-ready”
Status target: DELIVERY VALIDATION COMPLETE

Core truth:
- The local engine is already working.
- The remaining work is validation, UX hardening, and submission packaging.
- Do not expand scope. Close the remaining gates only.

FINAL ACCEPTANCE BAR
Axiom is DONE only when all of these are true:
[ ] ACP validated end-to-end in JetBrains AI Chat
[ ] Live OpenAI/Codex smoke passes with a real API key and structured output
[ ] CLI supports both planned input modes:
    - --bug + --test
    - --stacktrace + --function
[ ] ACP prompt parsing handles pasted bug context, not just file-path syntax
[ ] Backup demo assets exist
[ ] Submission assets and repo packaging are complete
[ ] Golden-path demo rehearsed 3 times without surprises

======================================================================
PHASE 1 — LOCK SCOPE AND DEFINE “DONE”
======================================================================

Objective:
Stop treating “implemented locally” as “done against plan.”

What this phase does:
- freeze feature scope
- define exact remaining blockers
- create one closeout checklist file in the repo
- assign owners and deadlines

Owner:
Team lead / P4

Tasks:
1. Create docs/CLOSEOUT_CHECKLIST.md
2. Put the 7 acceptance items above into it
3. Add owner + status + proof column for each item
4. Freeze all non-closeout work

Rules:
- no new features
- no second bug work unless all blockers are closed
- no ACP registry work until ACP itself is proven in JetBrains
- no visual polish before validation

Verification gate:
[ ] docs/CLOSEOUT_CHECKLIST.md exists
[ ] every remaining blocker has one owner
[ ] team agrees the only remaining path is validation + packaging

If this gate fails:
- stop coding
- align on what “done” means before moving on

======================================================================
PHASE 2 — COMPLETE CLI PARITY
======================================================================

Objective:
Match the CLI behavior promised in the plan.

Owner:
P1 or whoever owns cli.py

Required final CLI modes:
1. Current mode:
   axiom-cli --bug path/to/file.py --test path/to/test.py
2. Missing planned mode:
   axiom-cli --stacktrace stacktrace.txt --function function.py
3. Optional convenience mode:
   axiom-cli --bug-report bug.txt --function function.py

Implementation tasks:
1. Extend cli.py argparse parser
2. Add mutually exclusive input groups
3. Support stacktrace file loading
4. Support direct function file loading
5. Normalize all inputs into one internal request model
6. Reuse the same pipeline output and Evidence Ledger

Behavior requirements:
- if user passes invalid combination, show helpful error
- if file missing, fail clearly
- if stacktrace empty, fail clearly
- if function file unreadable, fail clearly

Tests:
1. tests/test_cli.py
   - test_bug_test_mode_works
   - test_stacktrace_function_mode_works
   - test_invalid_arg_combinations_fail
   - test_missing_files_fail_cleanly

Manual verification:
- run Bug A through current bug/test path
- run same bug through stacktrace/function path
- compare resulting ledger
- both paths should reach a valid final status

Verification gate:
[ ] CLI accepts --stacktrace and --function
[ ] tests/test_cli.py passes
[ ] both CLI modes produce a valid Evidence Ledger
[ ] README examples updated to include both modes

If this gate fails:
- do not move to ACP parsing
- fix CLI parity first

======================================================================
PHASE 3 — HARDEN ACP PROMPT PARSING
======================================================================

Objective:
Make ACP usable in the real chat flow described by the plan.

Owner:
P1 + P2

Current problem:
- ACP currently expects path-style input
- planned UX requires pasted text:
  - failing test text
  - stacktrace text
  - bug report text
  - optionally pasted function code

Final supported prompt patterns:
A. Pasted function + pasted failing test
B. Pasted function + pasted stacktrace
C. Pasted bug report + pasted function
D. Path-driven form remains supported as fallback

Implementation tasks:
1. Add a parser module for ACP prompt extraction
2. Accept free-form user text
3. Detect likely blocks:
   - python code
   - stacktrace
   - pytest assertion output
   - plain-language bug report
4. Normalize into internal request model:
   - function_source
   - error_info
   - context
   - source_mode
5. Add graceful fallback when parse confidence is low:
   “I need either:
    - function code + failing test,
    - function code + stacktrace,
    - or bug report + function code.”

Suggested parsing rules:
- if code fence contains def ... => treat as function source
- if text contains “Traceback” or “AssertionError” => treat as error info
- if text contains “test_” and “assert” => likely failing test
- if only plain English exists => treat as bug report
- if multiple code blocks, choose the block containing target def if possible

Tests:
1. tests/test_agent_parsing.py
   - pasted code + failing test
   - pasted code + stacktrace
   - bug report + code
   - malformed input returns helpful guidance
2. Snapshot tests for parser output

Manual verification:
- run agent handler directly with sample pasted prompts
- verify normalized request is correct
- verify Evidence Ledger still renders

Verification gate:
[ ] pasted bug contexts parse correctly
[ ] malformed prompt gets graceful guidance
[ ] path-based mode still works
[ ] no crash on messy pasted text

If this gate fails:
- simplify parsing
- require a stricter input template
- do not keep chasing “general chat understanding”

======================================================================
PHASE 4 — LIVE OPENAI/CODEX VALIDATION
======================================================================

Objective:
Close the “model path is only partially real” gap.

Owner:
P2

Required outcome:
Prove that live Codex/OpenAI structured output works in this environment with a real key.

Tasks:
1. Ensure OPENAI_API_KEY is actually set
2. Update scripts/smoke_openai.py so it fails loudly if key missing
   - no silent skip
3. Add one structured-output smoke for:
   - bug classification
   - patch generation
4. Validate pydantic parsing for at least one real call
5. Save one successful sample output to docs/examples/openai_smoke_success.json

Expected minimum smoke tests:
A. Classification smoke
- input: Bug A code + failing test
- output: axiom=totality, confidence, rationale

B. Patch smoke
- input: Bug A function + failing test
- output: syntactically valid candidate patch

Required repo-side changes:
- scripts/smoke_openai.py returns nonzero on failure
- docs/OPENAI_VALIDATION.md created
- document exact model used and exact success criteria

Verification gate:
[ ] OPENAI_API_KEY present
[ ] classification smoke passes with real model
[ ] patch smoke passes with real model
[ ] output parses into schema
[ ] success artifact saved in docs/examples/

If this gate fails:
- shrink schema
- use smaller structured output object
- add one repair retry
- if still unstable, document fallback mode honestly:
  “Axiom supports deterministic fallback locally; live Codex validation remains partial”

Note:
This is a blocker for “plan complete.”

======================================================================
PHASE 5 — ACP VALIDATION IN JETBRAINS
======================================================================

Objective:
Close the single biggest acceptance gap: prove the product surface actually works in the IDE.

Owner:
P1 + one teammate as witness

What must be proven:
1. Axiom appears in JetBrains AI Chat agent picker
2. It can be selected
3. A real prompt can be sent
4. A full Evidence Ledger comes back
5. The golden-path bug can be run through the IDE flow

Manual validation script:
1. Open PyCharm or WebStorm with AI Assistant enabled
2. Ensure Codex is present in AI Chat as baseline
3. Add/install Axiom agent using current ACP setup
4. Confirm Axiom appears in agent list
5. Select Axiom
6. Paste:
   - function code
   - failing test or stacktrace
7. Run prompt
8. Confirm a real ledger comes back
9. Capture screenshot
10. Repeat once more for confidence

Artifacts to save:
- screenshot of Axiom in picker
- screenshot of selected agent
- screenshot of full ledger in AI Chat
- short notes on any quirks

Repo tasks:
1. docs/ACP_VALIDATION.md
   - exact installation steps
   - exact tested IDE version
   - exact tested prompt
   - screenshot filenames
2. README ACP setup section tightened
3. If manual install required, document exact steps clearly

Verification gate:
[ ] Axiom appears in picker
[ ] Axiom can be selected
[ ] one real prompt returns full ledger
[ ] screenshots captured
[ ] docs/ACP_VALIDATION.md complete

If this gate fails:
- ACP remains incomplete
- CLI remains primary demo path
- do not falsely claim full ACP delivery

======================================================================
PHASE 6 — BACKUP DEMO ASSETS
======================================================================

Objective:
Protect against live failure and satisfy submission needs.

Owner:
P4

Required assets:
1. 60-second backup demo video
2. Screenshots of:
   - VERIFIED
   - FALSIFIED
   - UNPROVEN
3. One final demo script
4. One final “if live breaks” fallback script

Tasks:
1. Record golden-path Bug A demo
2. Record one falsified/counterexample moment
3. Capture three ledger screenshots
4. Save under docs/assets/
5. Add filenames and usage notes to docs/SUBMISSION.md

Video content should show:
- failing test or bug
- Axiom run
- ledger result
- short narration
- no fluff

Verification gate:
[ ] backup video exists
[ ] 3 screenshots exist
[ ] demo script exists
[ ] fallback script exists
[ ] docs/SUBMISSION.md references all assets

If this gate fails:
- stop all polish work
- produce the assets immediately

======================================================================
PHASE 7 — SUBMISSION PACKAGING
======================================================================

Objective:
Make the repo and submission look complete and credible.

Owner:
P4 + one reviewer

Required packaging items:
1. LICENSE
2. Final README
3. Team info
4. Repo public confirmation
5. Submission checklist completion
6. Track statement
7. Setup and demo instructions
8. Honest limitations section

Tasks:
1. Add MIT LICENSE
2. Finalize README with:
   - project description
   - track
   - stack
   - quickstart
   - CLI usage
   - ACP usage
   - golden demo path
   - limitations
3. Add docs/SUBMISSION.md
4. Add docs/TEAM.md or section in README
5. Add “repo public” checkbox to closeout checklist
6. Add screenshots and video link
7. Add one-paragraph project description for submission form
8. Confirm open-source requirement is met

Remember:
The hackathon requires projects shown in the demo to be fully open source, started during the event, and submitted with a short one-minute demo video. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

Verification gate:
[ ] LICENSE exists
[ ] README final
[ ] team info present
[ ] video link ready
[ ] screenshots linked
[ ] submission paragraph ready
[ ] repo public confirmed
[ ] open-source requirement clearly satisfied

======================================================================
PHASE 8 — FINAL REHEARSAL AND SIGN-OFF
======================================================================

Objective:
Prove the project is not just packaged, but stable enough to present.

Owner:
All

Rehearsal protocol:
1. Run golden path 3 times
2. Run ACP path at least once if ACP validated
3. Run CLI fallback at least once
4. Time the full demo
5. Practice the 3-minute pitch
6. Practice the “live failure” fallback

Required outputs:
- one final “go / no-go” decision
- one final checklist sign-off

Verification gate:
[ ] golden path works 3 times
[ ] ACP demo works or is officially downgraded
[ ] CLI fallback works
[ ] pitch fits in time
[ ] one owner assigned to demo, one to Q&A

======================================================================
PRIORITY ORDER — DO NOT DEVIATE
======================================================================

1. CLI parity
2. ACP prompt parsing
3. Live OpenAI validation
4. JetBrains ACP validation
5. Backup assets
6. Submission packaging
7. Rehearsal

If you are short on time:
- keep CLI working
- keep Evidence Ledger strong
- keep Bug A perfect
- document ACP honestly if still partial

======================================================================
FINAL DEFINITION OF DONE
======================================================================

Axiom is DONE when:
- the engine works locally
- the CLI matches plan
- Codex live validation is proven
- ACP is proven in JetBrains OR explicitly downgraded and documented
- submission assets exist
- packaging is complete
- the team has rehearsed

Until then:
Prototype complete. Delivery validation incomplete.




FOLLOW UP PLAN 2:

COMPLETE CLOSEOUT PLAN — FROM CURRENT STATE TO DELIVERY-READY
=============================================================

Goal
----
Take the repo from “repo-side closeout mostly done” to “fully validated, packaged, rehearsed, and ready to deliver,” with clear phases, owners, checkpoints, blockers, and exit criteria.

Current State
-------------
Already done:
- CLI parity is in place:
  - `--bug + --test`
  - `--stacktrace + --function`
  - `--bug-report + --function`
- Invalid combinations and missing/empty files are handled cleanly
- Pipeline accepts file-backed or pasted function input
- ACP prompt parsing is hardened and wired in
- OpenAI smoke now fails loudly without `OPENAI_API_KEY`
- Closeout/submission docs and packaging were added
- Verification already achieved:
  - `make test` -> 21 passed
  - `make verify-acp` -> passes import smoke
  - `axiom-cli --stacktrace ... --function demo_repo/checkout/discount.py` -> valid ledger
  - `scripts/smoke_openai.py` -> exits nonzero without key

Still blocked / not done:
- JetBrains ACP end-to-end validation in IDE
- Live OpenAI structured-output validation with real API key
- Demo assets:
  - screenshots
  - 60-second backup video
- Manual rehearsal
- Final sign-off / delivery validation complete

Definition of Done
------------------
The project is done only when all of the following are true:
1. Repo tests are green
2. CLI modes are verified end-to-end
3. ACP flow is validated inside the IDE
4. OpenAI smoke passes with a real key and structured output is confirmed
5. Screenshots + short demo video exist and are usable
6. README / submission docs exactly match shipped behavior
7. A full rehearsal has been completed
8. Final checklist is fully checked off
9. Delivery artifact is frozen and ready for handoff

Execution Strategy
------------------
Do this in 7 phases, in order:

PHASE 1 — Stabilize the repo and finish automated validation
PHASE 2 — Exhaustively verify user-facing flows
PHASE 3 — Perform external/manual validations
PHASE 4 — Produce demo and backup assets
PHASE 5 — Align documentation with reality
PHASE 6 — Rehearse the delivery
PHASE 7 — Freeze, package, and sign off

------------------------------------------------------------
PHASE 1 — STABILIZE THE REPO
------------------------------------------------------------

Objective
---------
Finish all repo-local cleanup so the codebase is stable before external validation begins.

Tasks
-----
1. Wait for the full test run to finish
2. Fix any failures, flakes, or warnings that appear
3. Re-run:
   - `make test`
   - `make verify-acp`
4. Run targeted CLI spot checks for every supported input combination
5. Confirm all docs referenced in the repo actually exist and are up to date
6. Confirm no stale TODOs or placeholders remain in docs or scripts

Validation matrix
-----------------
A. CLI input modes
- bug + test
- stacktrace + function
- bug-report + function

B. Function input modes
- function file path
- pasted function text

C. Prompt parser modes
- pasted function + failing test
- pasted function + stacktrace
- bug report + function
- path-driven fallback

D. Failure modes
- missing file
- empty file
- incompatible flags
- bad flag combinations
- no OpenAI key
- malformed inputs

Deliverables
------------
- Clean green local test run
- No known repo-local issues
- Updated issue list if anything remains

Exit criteria
-------------
- All automated tests pass
- No unexplained failures or flaky behavior remain
- CLI and parser behavior match docs

------------------------------------------------------------
PHASE 2 — EXHAUSTIVE FLOW VALIDATION
------------------------------------------------------------

Objective
---------
Validate the actual user journeys, not just unit tests.

Tasks
-----
Create a flow-verification checklist and run each path end-to-end.

Flow 1 — Stacktrace + function path
- Input stacktrace file
- Input function by file
- Verify CLI accepts input
- Verify parser builds correct task
- Verify pipeline runs
- Verify ledger output is structurally correct
- Verify output is understandable to a user

Flow 2 — Pasted function + stacktrace
- Paste function directly
- Feed stacktrace
- Verify parser does not misclassify content
- Verify resulting ledger remains valid

Flow 3 — Bug + test
- Feed bug description
- Feed failing test
- Verify pipeline produces expected diagnosis path

Flow 4 — Bug report + function
- Feed plain bug report
- Feed function input
- Verify prompt path is correct

Flow 5 — Bad input behavior
- Missing test file
- Empty stacktrace file
- Empty function file
- Invalid flag combinations
- Garbage input
- Very short input
- Very large input if supported

For each flow, capture:
- command used
- expected behavior
- actual behavior
- pass/fail
- notes / follow-up fixes

Deliverables
------------
- `docs/VALIDATION_MATRIX.md` or equivalent notes
- Flow-by-flow pass/fail record
- Known limitations list if any remain

Exit criteria
-------------
- Every supported user flow has been exercised manually at least once
- Every major failure mode has been checked
- Any mismatch between docs and reality is identified

------------------------------------------------------------
PHASE 3 — EXTERNAL / MANUAL VALIDATION
------------------------------------------------------------

Objective
---------
Complete the validations that cannot be proved from repo-only tests.

PART A — JetBrains ACP IDE validation
-------------------------------------
Goal:
Verify the ACP workflow works from the actual IDE environment, not just import smoke.

Tasks:
1. Set up clean IDE environment
2. Install or configure ACP integration
3. Open the demo project / repo
4. Trigger the intended flows from the IDE
5. Confirm prompt parsing behaves as expected
6. Confirm agent execution works
7. Confirm resulting output/ledger is visible and correct
8. Record screenshots while doing this
9. Note any differences between IDE behavior and CLI behavior

What to verify:
- ACP loads correctly
- Prompt payload reaches parser correctly
- pasted function flows work
- stacktrace flows work
- bug report flows work
- fallback path still works
- no environment-specific crash or path issue

Evidence to collect:
- screenshot of ACP running
- screenshot of successful result
- screenshot of any settings/config needed
- notes for reproduction

Exit criteria:
- At least one clean successful ACP end-to-end run in the IDE
- Reproducible setup steps documented

PART B — Live OpenAI structured-output validation
-------------------------------------------------
Goal:
Verify real API-backed behavior with a valid key.

Tasks:
1. Export or inject real `OPENAI_API_KEY`
2. Run `scripts/smoke_openai.py`
3. Confirm it passes
4. Inspect actual structured output carefully
5. Confirm schema / field expectations match downstream usage
6. Test at least one real path that exercises the same output handling as production flow
7. Record exact pass conditions in `docs/OPENAI_VALIDATION.md`

What to verify:
- auth works
- script exits zero
- structured output shape is correct
- parser/consumer accepts output
- errors are loud and actionable if something breaks

Evidence to collect:
- terminal output
- optional sanitized snippet of structured response
- success criteria checklist

Exit criteria:
- smoke passes with real key
- structured output is confirmed valid
- docs updated with exact validation steps and expected result

------------------------------------------------------------
PHASE 4 — DEMO ASSETS AND BACKUP MATERIALS
------------------------------------------------------------

Objective
---------
Create everything needed to show the system working even if live demo conditions fail.

Asset list
----------
Must-have:
- 3–6 screenshots
- 60-second backup demo video
- one short “happy path” demo script
- one fallback demo script if live system fails

Recommended screenshots
-----------------------
1. CLI invocation for stacktrace + function
2. Valid output ledger/result
3. ACP inside IDE
4. OpenAI smoke success with key
5. README or docs page showing supported flows
6. Optional error-handling screenshot showing clean failure mode

60-second backup demo video outline
-----------------------------------
0–10 sec:
- show repo / project name and goal

10–25 sec:
- show one CLI invocation

25–40 sec:
- show result / ledger / structured output

40–50 sec:
- show ACP or IDE integration briefly

50–60 sec:
- show docs / closeout / validation evidence

Rules for the video
-------------------
- keep it short
- no dead time
- no typing-heavy sections if avoidable
- zoom in on key output
- use stable terminal / font size
- no sensitive keys or secrets visible

Deliverables
------------
- final screenshots in `docs/assets/`
- final backup video
- short narration or caption outline
- exact filenames documented

Exit criteria
-------------
- A reviewer can understand the system from assets alone
- You can survive a failed live demo using the backup materials

------------------------------------------------------------
PHASE 5 — DOCUMENTATION HARDENING
------------------------------------------------------------

Objective
---------
Make sure the written story matches the real shipped behavior exactly.

Docs to review
--------------
- `README.md`
- `docs/SUBMISSION.md`
- `docs/CLOSEOUT_CHECKLIST.md`
- `docs/OPENAI_VALIDATION.md`
- `docs/ACP_VALIDATION.md`
- `docs/TEAM.md`
- `docs/examples/README.md`
- `docs/assets/README.md`

Documentation pass checklist
----------------------------
For each doc, verify:
- commands are correct
- file paths are correct
- examples actually work
- no stale wording remains
- all supported input combinations are described correctly
- limitations are stated honestly
- manual/external blockers are clearly separated from completed work

Specific documentation tasks
----------------------------
1. README
- Confirm supported CLI combinations are listed exactly
- Add one minimal example per major flow
- Document error behavior clearly

2. Submission doc
- Make sure it matches actual repo state
- Link to validation docs and assets cleanly

3. OpenAI validation doc
- Include both:
  - expected failure mode with no key
  - expected success mode with real key

4. ACP validation doc
- Include IDE setup
- Include exact reproduction steps
- Include screenshots if possible

5. Closeout checklist
- Split into:
  - completed
  - pending manual/external
  - blockers
  - final sign-off items

Exit criteria
-------------
- Docs are accurate enough that someone else could reproduce your validation
- No important behavior exists only in your head

------------------------------------------------------------
PHASE 6 — REHEARSAL
------------------------------------------------------------

Objective
---------
Prove the delivery can be presented clearly, quickly, and reliably.

Rehearsal format
----------------
Do 3 passes:

Pass 1 — Technical rehearsal
- Run commands exactly as planned
- Measure timing
- Identify friction points
- Fix rough edges

Pass 2 — Narrative rehearsal
- Explain:
  - what problem the tool solves
  - what flows it supports
  - what was added in this delivery phase
  - what is validated vs still manual
- Tighten wording

Pass 3 — Failure rehearsal
- Assume live OpenAI or ACP demo fails
- Use screenshots and backup video instead
- Practice switching smoothly to fallback

Demo script structure
---------------------
1. What changed
2. What now works
3. Evidence:
   - tests
   - CLI flow
   - ACP validation
   - OpenAI validation
4. Remaining manual dependencies
5. Why this is delivery-ready

Rehearsal checklist
-------------------
- all commands copied and ready
- demo inputs prepared
- terminal cleaned
- unnecessary windows closed
- backup screenshots accessible
- backup video accessible
- no secrets visible
- story fits target time

Exit criteria
-------------
- You can run the demo once cleanly
- You can still complete the demo if one dependency fails
- Talking points are concise and credible

------------------------------------------------------------
PHASE 7 — FINAL FREEZE AND SIGN-OFF
------------------------------------------------------------

Objective
---------
Create the final handoff state and stop changing things unless critical.

Tasks
-----
1. Re-run final verification:
   - `make test`
   - `make verify-acp`
   - `scripts/smoke_openai.py` with key if available
2. Confirm all docs are updated
3. Confirm all assets are in place
4. Complete `docs/CLOSEOUT_CHECKLIST.md`
5. Mark anything still pending explicitly
6. Freeze demo commands and inputs
7. Create final summary note for delivery
8. Tag or snapshot final commit if needed

Final summary should state
--------------------------
- what is complete
- what was validated automatically
- what was validated manually
- what remains external/manual
- what evidence exists for each item

Exit criteria
-------------
- No ambiguity about readiness
- No silent blockers
- Everything needed for review/demo/delivery is present

============================================================
DETAILED TASK BREAKDOWN
============================================================

WORKSTREAM A — CODE / BEHAVIOR
------------------------------
- [ ] Wait for full test run
- [ ] Fix any failures from full run
- [ ] Re-run local tests
- [ ] Re-run CLI happy-path checks
- [ ] Re-run CLI failure-mode checks
- [ ] Confirm prompt parser edge cases
- [ ] Confirm pipeline accepts both pasted and file-backed function input
- [ ] Confirm no regression in fallback path

WORKSTREAM B — OPENAI VALIDATION
--------------------------------
- [ ] Acquire real API key
- [ ] Run smoke script with real key
- [ ] Validate structured output shape
- [ ] Record results in docs
- [ ] Capture screenshot / evidence
- [ ] Confirm nonzero exit without key still works as intended

WORKSTREAM C — ACP / IDE VALIDATION
-----------------------------------
- [ ] Open IDE
- [ ] Configure ACP environment
- [ ] Run at least one end-to-end scenario
- [ ] Validate behavior matches docs
- [ ] Capture screenshots
- [ ] Document exact setup and reproduction steps

WORKSTREAM D — ASSETS
---------------------
- [ ] Capture terminal screenshots
- [ ] Capture ACP screenshots
- [ ] Capture OpenAI validation screenshot
- [ ] Record 60-second backup demo video
- [ ] Store assets in expected docs path
- [ ] Verify filenames and references

WORKSTREAM E — DOCUMENTATION
----------------------------
- [ ] README final pass
- [ ] Submission doc final pass
- [ ] Validation docs final pass
- [ ] Closeout checklist update
- [ ] Add known limitations if needed
- [ ] Confirm docs match final behavior

WORKSTREAM F — DELIVERY READINESS
---------------------------------
- [ ] Rehearse live demo
- [ ] Rehearse fallback demo
- [ ] Prepare final status summary
- [ ] Freeze final state
- [ ] Final sign-off

============================================================
SUGGESTED ORDER OF OPERATIONS
============================================================

Day / Block 1 — Stabilization
- wait for full test run
- fix anything failing
- rerun tests
- validate CLI flows

Day / Block 2 — External validations
- run JetBrains ACP validation
- run OpenAI validation with real key
- record evidence

Day / Block 3 — Demo assets + docs
- capture screenshots
- record backup video
- update docs to match final reality

Day / Block 4 — Rehearsal + freeze
- rehearse
- complete checklist
- write final delivery summary
- freeze final package

============================================================
RISK REGISTER
============================================================

Risk 1 — ACP works in import smoke but fails in actual IDE
Mitigation:
- validate early in Phase 3
- document setup precisely
- keep screenshot evidence

Risk 2 — OpenAI smoke passes differently than expected with real key
Mitigation:
- validate structured output explicitly
- inspect actual payload
- update docs immediately

Risk 3 — Docs drift from shipped behavior
Mitigation:
- do a dedicated doc pass after validation, not before
- verify every command by actually running it

Risk 4 — Live demo fails
Mitigation:
- backup screenshots
- backup 60-second video
- fallback script rehearsed

Risk 5 — Last-minute repo changes create regressions
Mitigation:
- freeze after final pass
- only accept critical fixes after rehearsal

============================================================
MINIMUM ACCEPTABLE CLOSEOUT
============================================================

If time gets tight, the absolute minimum acceptable finish is:
- all repo tests green
- one verified CLI happy path
- one verified ACP end-to-end run
- one verified OpenAI smoke run with real key
- screenshots captured
- backup video recorded
- docs updated
- closeout checklist completed

Anything less than that is still partial closeout, not full delivery validation.

============================================================
FINAL STATUS TEMPLATE
============================================================

Use this at the end:

Closeout status: READY / NEAR-READY / NOT READY

Completed:
- repo-side implementation complete
- CLI flows validated
- tests passing
- ACP validated
- OpenAI validated
- docs aligned
- backup assets captured
- rehearsal complete

Remaining blockers:
- <none, or list explicitly>

Evidence:
- `make test`
- `make verify-acp`
- `scripts/smoke_openai.py`
- screenshots in `docs/assets/`
- backup demo video
- checklist in `docs/CLOSEOUT_CHECKLIST.md`

Decision:
- ready for delivery
or
- not ready until the remaining blockers are closed

============================================================
RECOMMENDED NEXT ACTIONS RIGHT NOW
============================================================

1. Let the full test run finish and fix anything that shakes out there
2. Immediately do the real OpenAI validation with a real key
3. Do the JetBrains ACP IDE end-to-end validation next
4. Capture screenshots while doing both
5. Record the 60-second backup video
6. Update the validation docs with exact observed behavior
7. Rehearse once live and once with fallback
8. Complete the closeout checklist and freeze the delivery



FOLLOW UP PLAN 3:

Here’s a cleaner, more polished version you can use:

I’ve now locked the validation matrix using real command evidence and converted that into repo artifacts. The current pass adds a flow-by-flow validation log, splits the closeout checklist by completion state, and tightens the demo/checklist scripts so they match the current product surface exactly.

What I added:

docs/VALIDATION_MATRIX.md now captures real command results for:
make test
make verify-acp
make verify-crosshair
make demo
make demo-falsified
make demo-unproven
--stacktrace + --function
--bug-report + --function
key failure modes
docs/CLOSEOUT_CHECKLIST.md is now split into:
completed repo-local work
pending manual/external validation
current blockers
rehearsal log and final sign-off
docs/SUBMISSION.md now references the validation log as part of the delivery story
scripts/record_demo_checklist.sh now matches the shipped demo commands and fallback path

What I re-verified:

make test → passes
make verify-acp → passes import smoke
make verify-crosshair → verified case passes and falsified case yields a witness
make demo → VERIFIED
make demo-falsified → FALSIFIED
make demo-unproven → UNPROVEN
axiom-cli --stacktrace ... --function ... → valid ledger
axiom-cli --bug-report ... --function ... → valid ledger
expected CLI failure modes still fail clearly
scripts/smoke_openai.py still fails loudly without OPENAI_API_KEY

The demo flow is now:

Show the failing discount test
Run make demo
Show the VERIFIED ledger
Run make demo-falsified and show the concrete CrossHair witness
Run make demo-unproven to show the honest UNPROVEN path
If ACP fails live, switch immediately to the CLI and keep the ledger surface the same

What remains, and still cannot be closed from here:

JetBrains ACP end-to-end validation in the IDE
Live OpenAI structured-output validation with a real API key
Screenshots and 60-second backup video
Rehearsal and final freeze/sign-off

At this point, the repo is in a solid NEAR-READY state: local behavior is validated and documented, and the remaining open items are the manual/external ones called out in docs/CLOSEOUT_CHECKLIST.md.

Recommended next actions:

Run the IDE flow from docs/ACP_VALIDATION.md and capture screenshots
Run scripts/smoke_openai.py with a real key and save the JSON artifact
Capture the assets listed in docs/assets/README.md
Fill in rehearsal and sign-off in docs/CLOSEOUT_CHECKLIST.md

I can also turn this into a shorter Slack update or a more formal delivery-status note.


FOLLOW UP PLAN 4:

If scripts/smoke_openai.py is an API smoke test, it expects OpenAI API authentication and the standard API flow still uses Authorization: Bearer $OPENAI_API_KEY. Codex can authenticate with either a ChatGPT sign-in or an API key for the Codex CLI / IDE tools, but that is a Codex tool auth path, not automatically a substitute for an API-based smoke script in your repo. OpenAI’s Codex docs also recommend API-key auth for programmatic Codex CLI workflows like CI/CD.

So the practical answer is:

For the current smoke_openai.py gate: No, not unless you change the gate itself. If the script is validating live API structured output, you still need a real API key in that shell.
For developer workflow / repo work: Yes, you can use Codex instead of a raw API key for coding, code review, repo inspection, and IDE/CLI assistance, because Codex supports ChatGPT-account sign-in.
For a replacement validation path: only if you explicitly redefine the closeout criteria from “OpenAI API smoke passes” to something like “Codex-authenticated workflow passes.” That is a product/process decision, not an equivalent technical validation. Codex auth and API validation prove different things.

The cleanest framing for the repo would be:

“Could we use Codex for development and demo support? Yes. Could it close the existing OpenAI API validation gate without changes? No.”

A good next move is to split the gate into two separate validations:

Codex-assisted workflow validation
Confirms the project works with Codex CLI / IDE login via ChatGPT or API key. Codex supports both sign-in methods.
Live OpenAI API validation
Confirms scripts/smoke_openai.py can hit the OpenAI API and validate structured output with OPENAI_API_KEY.

That keeps the repo honest:

Codex can cover developer/operator workflow.
The API key gate still covers real API integration.

A concise note you could put in the repo:

Codex can be used for repo work, CLI assistance, and IDE-based workflows via ChatGPT sign-in or API-key auth, but it does not automatically satisfy the live OpenAI API validation gate. The current `scripts/smoke_openai.py` check still requires `OPENAI_API_KEY` because it validates direct API structured-output behavior rather than Codex tool authentication.

I can also rewrite docs/OPENAI_VALIDATION.md into a two-track validation doc: “Codex validation” vs “OpenAI API validation.”

It is already authniticated you just need to run codex or codex --yolo in the testminal

I’m checking the current official docs on Codex CLI auth and API validation so I can answer this cleanly against the actual tooling behavior.

Thought for 12s

Yes — if Codex is already authenticated in that terminal, you can use codex / codex --yolo for repo work, validation assistance, and command-running inside the project. The Codex CLI is designed to run in a terminal, inspect a repo, edit files, and run commands, and it supports ChatGPT-based sign-in as an auth method.

But that still does not automatically close the existing scripts/smoke_openai.py gate if that script is validating the OpenAI API directly. The OpenAI API docs are still explicit that API requests use OPENAI_API_KEY bearer auth, and the official SDKs/docs expect the key from the environment. So a Codex-authenticated shell and an API-authenticated Python smoke test are two different validation paths.

So the practical answer is:

Yes: use Codex now for repo tasks, command execution, cleanup, docs, and possibly a Codex-based validation workflow. Codex CLI can authenticate with ChatGPT or an API key.
No: Codex auth does not, by itself, replace OPENAI_API_KEY for a Python script that hits the OpenAI API.

The cleanest repo stance would be:

“Codex-authenticated validation is acceptable for local developer workflow and repo assistance. Live OpenAI API validation remains a separate gate and still requires OPENAI_API_KEY unless we intentionally redefine that closeout criterion.”

One important limitation on my side: I cannot run codex in your terminal from here. I can help you define exactly what to run and how to update the repo/docs so the distinction is explicit.

A concise repo note you could add:

Codex can be used for authenticated local repo work and command execution via ChatGPT or API-key sign-in. However, this does not replace the live OpenAI API validation gate: `scripts/smoke_openai.py` still requires `OPENAI_API_KEY` unless that gate is intentionally redefined to validate a Codex-based workflow instead.

I can rewrite docs/OPENAI_VALIDATION.md into a two-track version next: Codex validation vs OpenAI API validation.

Can you do both codex and OpenAI Key>

I’m checking the current official docs so I can answer precisely how these two auth paths can coexist and what each one validates.

Thought for 8s

Yes — that’s the cleanest setup.

You can use Codex auth for local repo work, command execution, and IDE/CLI assistance, while also using OPENAI_API_KEY for the repo’s live API smoke gate. OpenAI’s Codex docs say the CLI/IDE tools support either ChatGPT sign-in or API-key sign-in, while the OpenAI API itself still uses API keys for authentication.

So the practical split is:

Codex: use it to inspect the repo, run commands, edit files, and help with validation/rehearsal from the terminal. The Codex CLI is built for exactly that workflow.
OpenAI API key: use it for scripts/smoke_openai.py or any direct API validation, because that path is validating real API behavior and bearer-key auth.

So yes, do both:

Run Codex for the developer/operator workflow in the authenticated terminal.
Set OPENAI_API_KEY for the live API validation gate.
Keep those as two separate validations in the docs, because they prove different things.

A good repo wording would be:

Validation is split into two tracks:
1. Codex-authenticated local workflow validation (repo inspection, command execution, and CLI/IDE-assisted development).
2. Live OpenAI API validation via `OPENAI_API_KEY` for `scripts/smoke_openai.py`.

Codex auth does not replace API-key validation; the two checks cover different surfaces and should both be recorded when available.

One limitation on my side: I can help you define the exact commands and docs updates, but I cannot directly run codex in your terminal from here.


This is the OpenAI key "[REDACTED - do not store real API keys in repo files]"



FOLLOW UP PLAN 5:

Yes — here’s the exact one-pass closeout for the remaining OpenAI API gate.

FINAL OPENAI GATE CLOSEOUT — ONE PASS
=====================================

Goal
----
Close the direct OpenAI API validation gate cleanly and leave the repo/docs in a consistent state.

Precondition
------------
A real `OPENAI_API_KEY` is available in this shell.

Step 1 — export the key
-----------------------
export OPENAI_API_KEY='YOUR_REAL_KEY'

Step 2 — run the live smoke
---------------------------
PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py

Expected result
---------------
- exits with code 0
- prints/records a successful structured-output validation
- writes the success artifact if the script supports it:
  - `docs/examples/openai_smoke_success.json`

Step 3 — verify the result artifact
-----------------------------------
Confirm these are true:
- the command exited successfully
- the JSON artifact exists
- the JSON is valid
- the output shape matches what the repo/docs say it should be

Useful checks:
--------------
echo $?
ls -l docs/examples/openai_smoke_success.json
python -m json.tool docs/examples/openai_smoke_success.json >/dev/null

Step 4 — update docs
--------------------
Update these files to reflect the successful run:

1. `docs/OPENAI_VALIDATION.md`
Add:
- command used
- date/run context
- success result
- artifact path
- note that direct API validation is now complete

2. `docs/VALIDATION_MATRIX.md`
Add a row for:
- `scripts/smoke_openai.py`
- auth mode: `OPENAI_API_KEY`
- observed result: PASS
- artifact: `docs/examples/openai_smoke_success.json`

3. `docs/CLOSEOUT_CHECKLIST.md`
Move direct OpenAI validation from:
- pending manual/external
to:
- completed

Step 5 — update delivery status
-------------------------------
In `docs/DELIVERY_STATUS.md`, change the state from:

- Codex workflow validation: complete
- OpenAI API validation: pending

to:

- Codex workflow validation: complete
- OpenAI API validation: complete

Step 6 — re-state remaining blockers
------------------------------------
After the API smoke passes, the remaining blockers should be only:

- JetBrains ACP end-to-end validation in the IDE
- screenshots / 60-second backup video
- rehearsal
- final freeze / sign-off

Step 7 — final wording to drop into the repo
--------------------------------------------
Use this status text:

Direct OpenAI API validation is now complete. `scripts/smoke_openai.py` was run with a real `OPENAI_API_KEY`, the structured-output check passed, and the success artifact was recorded in `docs/examples/openai_smoke_success.json`. Codex workflow validation and direct API validation are now both closed; the remaining open items are IDE validation, demo assets, rehearsal, and final sign-off.

Fast sanity checklist
---------------------
- [ ] `OPENAI_API_KEY` exported
- [ ] `scripts/smoke_openai.py` passed
- [ ] success JSON artifact exists
- [ ] `docs/OPENAI_VALIDATION.md` updated
- [ ] `docs/VALIDATION_MATRIX.md` updated
- [ ] `docs/CLOSEOUT_CHECKLIST.md` updated
- [ ] `docs/DELIVERY_STATUS.md` updated
- [ ] remaining blockers list reduced accordingly

And this is the exact order I’d use in terminal:

export OPENAI_API_KEY='YOUR_REAL_KEY'
PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py
echo $?
ls -l docs/examples/openai_smoke_success.json
python -m json.tool docs/examples/openai_smoke_success.json >/dev/null

Then update:

docs/OPENAI_VALIDATION.md
docs/VALIDATION_MATRIX.md
docs/CLOSEOUT_CHECKLIST.md
docs/DELIVERY_STATUS.md

After that, only the IDE/demo/rehearsal items should remain.

FOLLOW UP PLAN 6:

COMPLETE PROJECT PLAN — FROM CURRENT STATE TO FINAL DELIVERY
============================================================

What happened
-------------
The previous plan narrowed in on one blocker — the OpenAI validation gate — instead of covering the whole project end to end.

This plan is the full one:
- product surface
- repo hardening
- validation
- Codex track
- OpenAI API track
- JetBrains ACP track
- demo paths
- docs
- assets
- rehearsal
- final freeze and submission

Project Goal
------------
Ship a delivery-ready Axiom repo that:
- supports all intended CLI input modes
- produces a valid ledger surface consistently
- validates both local and external integration paths honestly
- has a reliable demo story, including fallback paths
- has complete docs, evidence, and sign-off artifacts

Current State
-------------
Already complete:
- CLI parity is in place
- parser / pipeline support pasted + file-backed function input
- key CLI flows work
- failure modes fail clearly
- CrossHair demo paths exist
- repo-local validation log exists
- Codex workflow validation is proven
- closeout docs/checklists exist
- demo script exists

Still open:
- direct OpenAI API validation with real `OPENAI_API_KEY`
- JetBrains ACP end-to-end validation in the IDE
- screenshots
- 60-second backup video
- rehearsal
- freeze / final sign-off

Definition of Done
------------------
The project is done only when all of these are true:

1. Repo tests pass
2. CrossHair verification flows pass
3. CLI supported modes are validated
4. Codex-authenticated workflow is validated
5. Direct OpenAI API smoke is validated with a real key
6. JetBrains ACP works in the actual IDE
7. Demo assets are captured
8. Docs match the shipped behavior exactly
9. Rehearsal is completed
10. Final checklist is signed off

============================================================
PHASE 1 — LOCK THE PRODUCT SURFACE
============================================================

Goal
----
Make sure the project scope is frozen and clearly defined before more validation work.

Scope to lock
-------------
Supported user-facing flows:
- `--bug + --test`
- `--stacktrace + --function`
- `--bug-report + --function`

Supported function sources:
- file-backed function input
- pasted function input

Supported outcomes:
- VERIFIED
- FALSIFIED
- UNPROVEN

Supported environments:
- CLI
- Codex-assisted terminal workflow
- JetBrains ACP IDE workflow
- OpenAI smoke validation path

Tasks
-----
- Confirm README and docs describe only the flows that actually exist
- Remove or mark any experimental/partial surfaces
- Freeze demo commands to the actual shipped set
- Ensure fallback path is explicit: ACP failure -> CLI path with same ledger surface

Deliverables
------------
- frozen supported-command list
- final demo commands
- final list of evidence-producing commands

Exit criteria
-------------
- no ambiguity about what the project claims to support

============================================================
PHASE 2 — REPO STABILIZATION
============================================================

Goal
----
Get the codebase into a clean, repeatable state before external/manual validation.

Tasks
-----
1. Run all repo-local checks again
   - `make test`
   - `make verify-acp`
   - `make verify-crosshair`
   - `make demo`
   - `make demo-falsified`
   - `make demo-unproven`

2. Re-run CLI validation commands
   - stacktrace + function
   - bug-report + function
   - bug + test if applicable

3. Re-run all important failure modes
   - missing files
   - empty files
   - incompatible flags
   - malformed inputs

4. Fix anything flaky or inconsistent
5. Confirm output ledger stays structurally consistent across happy paths and fallback paths

Deliverables
------------
- green local validation state
- updated validation matrix if any command changed
- stable repo behavior

Exit criteria
-------------
- all local commands pass or fail exactly as documented
- no known local blockers remain

============================================================
PHASE 3 — FULL VALIDATION MATRIX
============================================================

Goal
----
Turn the current evidence into a complete, auditable validation story.

Validation tracks
-----------------
A. Repo-local behavior
B. CLI flows
C. CrossHair demo flows
D. Codex-authenticated workflow
E. Direct OpenAI API validation
F. JetBrains ACP validation
G. Manual/demo assets
H. Rehearsal and sign-off

Tasks
-----
For each track, record:
- command / action
- environment
- expected outcome
- observed outcome
- artifact/evidence
- status: complete / pending / blocked

Make sure `docs/VALIDATION_MATRIX.md` includes:
- `make test`
- `make verify-acp`
- `make verify-crosshair`
- `make demo`
- `make demo-falsified`
- `make demo-unproven`
- CLI `--stacktrace + --function`
- CLI `--bug-report + --function`
- CLI failure modes
- Codex smoke command
- OpenAI smoke command
- ACP IDE run
- screenshots / video capture
- rehearsal completion

Deliverables
------------
- a truly complete validation matrix
- no hidden validation assumptions

Exit criteria
-------------
- every claimed surface has a corresponding validation row

============================================================
PHASE 4 — CODEX WORKFLOW TRACK
============================================================

Goal
----
Use Codex as the authenticated local workflow validation track.

What this proves
----------------
- Codex is installed and usable
- Codex can run non-interactive repo tasks in this environment
- Codex-assisted developer workflow is real

What it does NOT prove
----------------------
- direct OpenAI API auth
- direct API structured-output behavior
- IDE ACP flow

Tasks
-----
- Keep the successful Codex smoke command in the validation log
- Document Codex as a separate validation track in:
  - `docs/OPENAI_VALIDATION.md`
  - `docs/VALIDATION_MATRIX.md`
  - `docs/CLOSEOUT_CHECKLIST.md`
  - `docs/DELIVERY_STATUS.md`
  - `docs/SUBMISSION.md`

Suggested proof command
-----------------------
- `codex exec -C <repo> --skip-git-repo-check "Reply with exactly: codex-ok"`

Deliverables
------------
- Codex workflow track marked complete
- docs clearly separate Codex vs direct API validation

Exit criteria
-------------
- no one can confuse “Codex works” with “OpenAI API smoke passed”

============================================================
PHASE 5 — DIRECT OPENAI API TRACK
============================================================

Goal
----
Close the real API validation gate honestly.

What this proves
----------------
- API auth works with `OPENAI_API_KEY`
- `scripts/smoke_openai.py` runs successfully
- structured-output path works in reality, not just in theory

Tasks
-----
1. Export a real key:
   - `export OPENAI_API_KEY='...'`

2. Run the smoke:
   - `PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py`

3. Verify:
   - exit code is zero
   - success artifact exists if expected
   - JSON/output is valid
   - output shape matches docs and downstream assumptions

4. Save evidence:
   - terminal output
   - JSON artifact
   - validation matrix row
   - checklist update

Docs to update
--------------
- `docs/OPENAI_VALIDATION.md`
- `docs/VALIDATION_MATRIX.md`
- `docs/CLOSEOUT_CHECKLIST.md`
- `docs/DELIVERY_STATUS.md`

Deliverables
------------
- direct API validation marked complete
- success artifact recorded

Exit criteria
-------------
- real OpenAI API smoke passes with a real key

============================================================
PHASE 6 — JETBRAINS ACP IDE TRACK
============================================================

Goal
----
Prove the project works in the actual IDE flow, not just at import level.

What this proves
----------------
- ACP integration works in practice
- prompt parsing survives real IDE invocation
- the user-facing IDE experience is real

Tasks
-----
1. Open the repo in JetBrains
2. Configure ACP exactly as documented
3. Run at least one end-to-end supported flow
4. Confirm the agent produces the expected ledger/result
5. Confirm no path/config differences break the flow
6. Capture screenshots
7. Update `docs/ACP_VALIDATION.md` with exact observed setup and behavior

Minimum ACP scenarios
---------------------
- one happy path from IDE
- one confirmation that fallback to CLI is available if IDE flow fails live

Evidence to collect
-------------------
- IDE screenshot showing ACP configured
- IDE screenshot showing successful output
- notes on setup steps
- any environment caveats

Deliverables
------------
- ACP validation doc updated
- screenshots stored in `docs/assets/`
- checklist row marked complete

Exit criteria
-------------
- one successful reproducible IDE run is documented

============================================================
PHASE 7 — DEMO DESIGN
============================================================

Goal
----
Create a live demo and a fallback demo that tell the same story.

Primary live demo
-----------------
1. Show the failing discount test
2. Run `make demo`
3. Show VERIFIED ledger
4. Run `make demo-falsified`
5. Show concrete CrossHair witness
6. Run `make demo-unproven`
7. Show honest UNPROVEN path
8. Optionally show ACP path briefly
9. If ACP fails, switch immediately to CLI while keeping the same ledger/result surface

Demo principles
---------------
- same surface across CLI and fallback
- no hidden magic
- keep it fast
- show honest outcomes, not only happy paths

Tasks
-----
- finalize `scripts/record_demo_checklist.sh`
- make sure every command shown in demo is already validated
- prepare copy/paste command block
- prep fallback path commands
- prep clean terminal state

Deliverables
------------
- frozen demo script
- fallback script
- command checklist

Exit criteria
-------------
- you can demo the project end to end without improvising

============================================================
PHASE 8 — ASSETS
============================================================

Goal
----
Create backup evidence so the project is still reviewable if the live demo fails.

Required assets
---------------
- screenshot of failing test
- screenshot of VERIFIED result
- screenshot of FALSIFIED witness
- screenshot of UNPROVEN result
- screenshot of Codex workflow proof
- screenshot of ACP IDE flow
- screenshot of OpenAI smoke success
- 60-second backup video

Video outline
-------------
0–10s: what the project is
10–25s: failing test + `make demo`
25–35s: VERIFIED ledger
35–45s: falsified witness
45–52s: UNPROVEN path
52–60s: ACP / Codex / docs / readiness summary

Tasks
-----
- capture screenshots into `docs/assets/`
- record short video
- make sure no secrets are visible
- add filenames and descriptions to `docs/assets/README.md`

Deliverables
------------
- screenshots
- backup video
- assets README updated

Exit criteria
-------------
- a reviewer can understand the project even without a live run

============================================================
PHASE 9 — DOCUMENTATION HARDENING
============================================================

Goal
----
Make docs reflect the exact real project state.

Docs to finalize
----------------
- `README.md`
- `docs/SUBMISSION.md`
- `docs/VALIDATION_MATRIX.md`
- `docs/CLOSEOUT_CHECKLIST.md`
- `docs/OPENAI_VALIDATION.md`
- `docs/ACP_VALIDATION.md`
- `docs/DELIVERY_STATUS.md`
- `docs/assets/README.md`
- `docs/examples/README.md`

Tasks
-----
For each document:
- verify every command exists and runs
- verify every path/file name is correct
- verify every claim has evidence
- separate:
  - complete
  - pending
  - blocked
- make sure Codex vs API-key validation is clearly distinguished
- make sure demo commands exactly match shipped commands

Deliverables
------------
- fully aligned documentation set

Exit criteria
-------------
- someone else could reproduce the whole closeout from docs alone

============================================================
PHASE 10 — REHEARSAL
============================================================

Goal
----
Prove you can present the project reliably.

Rehearsal passes
----------------
Pass 1 — technical
- run the actual commands
- check timing
- fix rough edges

Pass 2 — narrative
- explain what the tool does
- explain supported flows
- explain VERIFIED / FALSIFIED / UNPROVEN
- explain Codex vs API vs ACP validation

Pass 3 — failure mode
- pretend ACP fails
- switch to CLI
- pretend API gate cannot be shown live
- use screenshot/video evidence

Deliverables
------------
- rehearsal notes
- updated checklist
- final short spoken walkthrough

Exit criteria
-------------
- live and fallback demo both work cleanly

============================================================
PHASE 11 — FINAL FREEZE
============================================================

Goal
----
Stop changing the project and produce the final handoff state.

Tasks
-----
1. Re-run final validations
2. Confirm all artifacts exist
3. Confirm checklists are complete
4. Update delivery status to final state:
   - READY
   - NEAR-READY
   - NOT READY
5. Freeze commands, assets, and docs
6. Tag or snapshot if needed
7. Prepare final handoff note

Deliverables
------------
- final repo state
- final delivery-status note
- final evidence set
- final checklist state

Exit criteria
-------------
- no open ambiguity about readiness

============================================================
SINGLE MASTER CHECKLIST
============================================================

CORE BEHAVIOR
-------------
- [ ] CLI modes confirmed
- [ ] parser modes confirmed
- [ ] pipeline modes confirmed
- [ ] failure modes confirmed

REPO VALIDATION
---------------
- [ ] `make test`
- [ ] `make verify-acp`
- [ ] `make verify-crosshair`
- [ ] `make demo`
- [ ] `make demo-falsified`
- [ ] `make demo-unproven`

CLI VALIDATION
--------------
- [ ] `--stacktrace + --function`
- [ ] `--bug-report + --function`
- [ ] `--bug + --test` if part of shipped surface
- [ ] invalid combos fail clearly
- [ ] missing/empty files fail clearly

CODEX TRACK
-----------
- [ ] Codex smoke command recorded
- [ ] Codex marked complete in docs
- [ ] Codex separated from API validation in docs

OPENAI API TRACK
----------------
- [ ] real `OPENAI_API_KEY` exported
- [ ] `scripts/smoke_openai.py` passes
- [ ] success artifact saved
- [ ] docs updated
- [ ] checklist updated

ACP TRACK
---------
- [ ] IDE configured
- [ ] one happy path run succeeds
- [ ] screenshots captured
- [ ] ACP doc updated

ASSETS
------
- [ ] failing test screenshot
- [ ] VERIFIED screenshot
- [ ] FALSIFIED screenshot
- [ ] UNPROVEN screenshot
- [ ] Codex screenshot
- [ ] ACP screenshot
- [ ] OpenAI smoke screenshot
- [ ] 60-second backup video

DOCS
----
- [ ] README final
- [ ] submission doc final
- [ ] validation matrix final
- [ ] closeout checklist final
- [ ] delivery status final
- [ ] assets README final

REHEARSAL / FREEZE
------------------
- [ ] technical rehearsal
- [ ] narrative rehearsal
- [ ] fallback rehearsal
- [ ] final freeze
- [ ] final sign-off

============================================================
BEST EXECUTION ORDER
============================================================

Order 1 — stabilize and confirm
- rerun all local validations
- lock commands
- update validation matrix

Order 2 — close external gates
- OpenAI API validation
- JetBrains ACP validation

Order 3 — capture evidence
- screenshots
- backup video

Order 4 — align docs
- update all docs to final truth

Order 5 — rehearse and freeze
- live run
- fallback run
- final sign-off

============================================================
HONEST FINAL STATES
============================================================

READY
-----
All validation tracks complete, assets captured, docs aligned, rehearsal done.

NEAR-READY
----------
Repo is clean and documented, but one or more external/manual gates remain open.

NOT READY
---------
Core repo behavior or major validation tracks are still incomplete.

Right now, based on what you shared, the project is:
- NEAR-READY

because:
- repo-local validation is strong
- Codex workflow is validated
- but OpenAI API, ACP IDE validation, assets, and final rehearsal are still open

============================================================
NEXT ACTIONS RIGHT NOW
============================================================

1. Re-run the local validation commands and confirm nothing changed
2. Close the OpenAI API gate with a real `OPENAI_API_KEY`
3. Run the JetBrains ACP flow in the real IDE
4. Capture all screenshots during those runs
5. Record the 60-second backup video
6. Do one full rehearsal
7. Mark final checklist and freeze the repo

FOLLOW UP PLAN 7:

MANUAL CLOSEOUT PACK — FINAL STEPS TO GO FROM NEAR-READY TO READY
=================================================================

Current honest state
--------------------
The repo is NEAR-READY.

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

============================================================
PART 1 — EXACT ACP CLOSEOUT RUN
============================================================

Goal
----
Produce one real, reproducible JetBrains ACP success and record it.

What to prepare
---------------
- JetBrains IDE open on the repo
- ACP configured as described in `docs/ACP_VALIDATION.md`
- one known-good demo target ready
- terminal available in case fallback to CLI is needed
- screenshot tool ready

Recommended ACP validation scenario
-----------------------------------
Use the simplest supported happy path that matches the shipped surface.

Preferred scenario:
- use the discount demo / known verification path
- ask ACP to analyze the bug / verification case
- confirm it produces the expected ledger/result surface

Minimum evidence required
-------------------------
1. ACP is visible in the IDE
2. repo/project is visible
3. prompt or invocation is visible
4. successful result is visible
5. result is consistent with the expected product surface

ACP run checklist
-----------------
- [ ] Open project in JetBrains
- [ ] Confirm ACP plugin/integration is enabled
- [ ] Confirm repo indexes/load are complete
- [ ] Start one supported end-to-end flow
- [ ] Wait for result
- [ ] Confirm output is a valid expected result
- [ ] Capture screenshots
- [ ] Record exact notes in `docs/ACP_VALIDATION.md`

What to record in docs/ACP_VALIDATION.md
----------------------------------------
Use this structure:

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

Suggested wording
-----------------
JetBrains ACP end-to-end validation was completed in the IDE on a real project checkout. A supported flow was executed successfully, and the resulting output matched the expected ledger/result surface. Screenshots were captured in `docs/assets/` and the reproduction notes below reflect the actual run conditions.

If ACP fails
------------
Do not fake success. Record it honestly.

Use this wording:
JetBrains ACP end-to-end validation was attempted but did not complete successfully in the IDE environment. The project remains demoable via the validated CLI fallback path, which preserves the same ledger/result surface. Failure details and environment notes are recorded below.

============================================================
PART 2 — EXACT SCREENSHOT LIST
============================================================

Goal
----
Capture only what is needed, with filenames that match the docs.

Required screenshots
--------------------
1. `01_failing_test.png`
- show the failing discount test or initial problem state

2. `02_demo_verified.png`
- show `make demo` producing VERIFIED

3. `03_demo_falsified.png`
- show `make demo-falsified` producing FALSIFIED
- include the concrete witness/counterexample if visible

4. `04_demo_unproven.png`
- show `make demo-unproven` producing UNPROVEN

5. `05_cli_stacktrace_function.png`
- show `axiom-cli --stacktrace ... --function ...`
- include valid ledger output

6. `06_cli_bugreport_function.png`
- show `axiom-cli --bug-report ... --function ...`
- include valid ledger output

7. `07_codex_smoke.png`
- show the successful Codex workflow smoke command/result

8. `08_openai_smoke_success.png`
- show the successful real OpenAI smoke validation

9. `09_acp_success.png`
- show the successful JetBrains ACP IDE run
- if ACP fails, replace with:
  - `09_acp_attempt.png`

Optional but useful
-------------------
10. `10_cli_failure_mode.png`
- show one cleanly handled invalid input / failure case

Screenshot rules
----------------
- no secrets visible
- no API keys visible
- zoom enough to read the important output
- crop out noise
- keep terminal font large enough
- do not include unrelated windows/tabs

What to update after capture
----------------------------
In `docs/assets/README.md`, list each screenshot with one line of explanation.

Suggested format
----------------
- `01_failing_test.png` — failing input/test state before demo
- `02_demo_verified.png` — VERIFIED result from `make demo`
- `03_demo_falsified.png` — FALSIFIED result with witness from `make demo-falsified`
- `04_demo_unproven.png` — UNPROVEN result from `make demo-unproven`
- `05_cli_stacktrace_function.png` — CLI stacktrace + function happy path
- `06_cli_bugreport_function.png` — CLI bug-report + function happy path
- `07_codex_smoke.png` — successful Codex workflow validation
- `08_openai_smoke_success.png` — successful direct OpenAI API smoke validation
- `09_acp_success.png` — successful JetBrains ACP end-to-end IDE validation

============================================================
PART 3 — 60-SECOND BACKUP VIDEO
============================================================

Goal
----
Create one short backup demo that tells the whole story if a live demo goes sideways.

Video structure
---------------
0–8 sec
- show repo/project name
- one sentence: what the tool does

8–18 sec
- show failing input/test

18–30 sec
- run or show `make demo`
- show VERIFIED

30–40 sec
- show `make demo-falsified`
- point to the witness/counterexample

40–48 sec
- show `make demo-unproven`
- point to honest UNPROVEN outcome

48–56 sec
- briefly show Codex / ACP / OpenAI validation evidence

56–60 sec
- close with “repo validated; remaining delivery evidence captured here”

Video rules
-----------
- no long typing
- no secrets
- no dead time
- keep cursor movement minimal
- use prepared windows/commands
- prefer cuts over scrolling

Recommended filename
--------------------
- `backup_demo_60s.mp4`

Update docs
-----------
Add it to `docs/assets/README.md`.

============================================================
PART 4 — EXACT REHEARSAL CHECKLIST
============================================================

Goal
----
Log a real rehearsal, not just intent.

Technical rehearsal checklist
-----------------------------
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

Narrative rehearsal checklist
-----------------------------
- [ ] can explain the project in 1–2 sentences
- [ ] can explain supported flows
- [ ] can explain VERIFIED / FALSIFIED / UNPROVEN clearly
- [ ] can explain Codex vs OpenAI API validation
- [ ] can explain ACP vs CLI fallback
- [ ] can explain what is complete vs what was manual

Failure-mode rehearsal checklist
--------------------------------
- [ ] practiced ACP failure fallback to CLI
- [ ] practiced not relying on live OpenAI during demo
- [ ] practiced using screenshots/video if needed
- [ ] practiced finishing the demo without improvising

What to write in docs/CLOSEOUT_CHECKLIST.md
-------------------------------------------
Use this template:

Rehearsal log
- Date:
- Environment:
- Rehearsal type: technical / narrative / fallback
- Result: PASS / PASS WITH NOTES / FAIL
- Notes:

Example
-------
Rehearsal log
- Date: 2026-04-18
- Environment: local terminal + JetBrains IDE
- Rehearsal type: technical + fallback
- Result: PASS WITH NOTES
- Notes: live flow worked; ACP fallback to CLI was also tested successfully; minor terminal resizing cleaned up before final demo.

============================================================
PART 5 — FINAL FREEZE / SIGN-OFF
============================================================

Goal
----
Move the repo from NEAR-READY to READY honestly.

Freeze checklist
----------------
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

What to write in docs/CLOSEOUT_CHECKLIST.md
-------------------------------------------
Final sign-off
- Date:
- Signed off by:
- Repo state:
- Status: READY / NEAR-READY / NOT READY
- Notes:

Suggested READY wording
-----------------------
Final sign-off
- Date: 2026-04-18
- Signed off by: <name>
- Repo state: delivery candidate frozen
- Status: READY
- Notes: repo-local validation, Codex workflow validation, direct OpenAI API validation, JetBrains ACP IDE validation, demo assets, and rehearsal have all been completed. The delivery surface is frozen and ready for handoff.

Suggested NEAR-READY wording
----------------------------
Final sign-off
- Date: 2026-04-18
- Signed off by: <name>
- Repo state: delivery candidate not yet frozen
- Status: NEAR-READY
- Notes: core repo validation is complete, but one or more manual/external closeout items remain open. See blockers above.

============================================================
PART 6 — EXACT DOC UPDATES AFTER MANUAL CLOSEOUT
============================================================

After ACP + assets + rehearsal are done, update these files:

1. `docs/ACP_VALIDATION.md`
Mark ACP validation complete and attach screenshot references.

2. `docs/assets/README.md`
List all real screenshots and the backup video.

3. `docs/CLOSEOUT_CHECKLIST.md`
Fill in:
- ACP completion
- screenshots/video completion
- rehearsal log
- final sign-off

4. `docs/DELIVERY_STATUS.md`
Change status from:
- NEAR-READY
to:
- READY

Suggested final status wording
------------------------------
The project is now READY. Repo-local behavior, CrossHair verification flows, CLI validation, Codex workflow validation, direct OpenAI API validation, and JetBrains ACP IDE validation are all complete. Demo assets have been captured, rehearsal has been logged, and the delivery surface is frozen for handoff.

5. `docs/SUBMISSION.md`
Make sure it references:
- validation matrix
- ACP validation notes
- assets list
- final delivery status

============================================================
PART 7 — FASTEST PATH TO READY
============================================================

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

============================================================
PART 8 — HONEST FINAL DECISION RULE
============================================================

Mark the project READY only if all of these are true:
- ACP run really happened
- screenshots/video really exist
- rehearsal really happened
- sign-off is really filled in

If any one of those is missing, leave it NEAR-READY.

============================================================
PART 9 — FINAL PASTE-READY STATUS NOTE
============================================================

Use this once the last manual steps are actually complete:

The remaining manual closeout steps are now complete. JetBrains ACP end-to-end validation was run and documented, demo screenshots and the backup video were captured, rehearsal was logged, and the final freeze/sign-off was recorded. At this point the project is READY: repo-local validation, Codex workflow validation, direct OpenAI API validation, IDE validation, assets, and closeout documentation are all in place.

If ACP fails and you need the honest version instead, use:

The repo remains NEAR-READY. Repo-local validation, Codex workflow validation, and direct OpenAI API validation are complete, but JetBrains ACP end-to-end validation did not complete successfully in the IDE environment. The CLI fallback path remains validated and demoable, and all open manual blockers are recorded in the closeout checklist.
