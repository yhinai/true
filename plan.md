# CORRECT-BY-CONSTRUCTION
# ONE-FILE MASTER EXECUTION PLAN
# Final merged plan
# Build philosophy: start tiny, working, truthful; then add one capability at a time

################################################################################
# 0. EXECUTIVE SUMMARY
################################################################################

Project name:
  Correct by Construction

One-line thesis:
  Codex is the proposal engine, not the source of trust.
  Trust comes from deterministic verification, staged execution, retry with
  evidence, honest verdicts, and benchmarked improvement over baseline.

Primary demo thesis:
  Same Codex. Same task. Same budget. Same environment.
  Our harness improves verified outcomes and reduces unsafe claims.

Primary product identity:
  This is not "another coding agent."
  This is a verification-first control plane around Codex.

Primary mechanism:
  1. Codex proposes a change or claims completion.
  2. Harness intercepts "done."
  3. Deterministic verifier runs task oracle / tests / checks.
  4. If verification fails, the harness retries with evidence.
  5. The system stops only when the oracle agrees or the budget is exhausted.
  6. Every run emits proof artifacts.
  7. Every new feature must preserve this working loop.

Creative framing:
  We treat AI coding like a verification problem:
    - oracles
    - assertions
    - failure modes
    - counterexamples
    - coverage
    - retry with evidence
    - proof artifacts

################################################################################
# 1. CORE BUILD PHILOSOPHY
################################################################################

This project must be built like a correct-by-construction bike.

That means:
  - Start with the smallest bike that actually rolls.
  - Prove it rolls.
  - Add exactly one meaningful part.
  - Re-test after every addition.
  - Never stack new complexity on a broken core.
  - Never rewrite if layering will do.
  - Every phase must end in a working, truthful, demoable system.

The growth model is:

  tiny truthful loop
    -> tiny benchmarked loop
    -> real file-backed loop
    -> stronger verifier loop
    -> curated benchmark loop
    -> plan-aware loop
    -> review-aware loop
    -> graph-aware loop
    -> test-growth loop
    -> multi-role loop
    -> IDE/product shell

Hard construction rule:
  Each phase = previous working system + one meaningful capability.

Not:
  Each phase = new architecture + new assumptions + partial rewrite.

################################################################################
# 2. TWO INVARIANTS
################################################################################

Product invariant:
  The system never claims success unless the deterministic verifier agrees.

Construction invariant:
  The next phase must not break the last working phase.

Every feature must satisfy both:
  - Does it preserve truthful verification?
  - Does it preserve the previously working loop?

If not, it does not ship in that phase.

################################################################################
# 3. NORTH STAR GOALS
################################################################################

Hackathon north star:
  Show a benchmark-backed and live-demo-backed reliability lift over Vanilla
  Codex.

Product north star:
  Build a reusable harness that can:
    - patch code
    - verify code
    - retry on evidence
    - grow tests
    - review diffs
    - gate merges
    - explain safety and risk
    - later expand into richer orchestration without rewrites

Construction north star:
  Every phase leaves behind a usable, benchmarkable, demoable system.

Demo-time must-haves:
  1. Baseline and treatment are clearly defined and fair.
  2. A curated benchmark subset has reproducible A/B results.
  3. We have 3 pre-verified golden demo tasks where treatment wins clearly.
  4. We have 1 live task with a rehearsed flow.
  5. Treatment emits a clear proof card and evidence ledger.
  6. We can explain the value in under 60 seconds.

Must-not-happen:
  1. Treatment is slower and less correct than baseline on the chosen subset.
  2. The verifier depends on an LLM saying "looks good."
  3. The demo depends on fragile late-stage plugin or subagent work.
  4. We over-promise full-benchmark dominance.

################################################################################
# 4. PRODUCT PRINCIPLES
################################################################################

Principles:
  1. Proposal != trust.
  2. Deterministic verification is the source of truth.
  3. Retry-with-evidence is the product core.
  4. The moat is the verification core, not the role pattern.
  5. Roles are orchestration layers, not the trust source.
  6. Every phase has one stable demo flow.
  7. Every phase has one reproducible command path.
  8. Every phase has one checked-in artifact example.
  9. Benchmarking begins early in a tiny way and grows with the system.
 10. Contracts/CrossHair are accelerators, not blockers.
 11. IDE is a thin shell, never the core.
 12. Subagents come last, not first.
 13. Add only one hard thing per phase.
 14. Preserve forward compatibility without overbuilding.
 15. Freeze behavior early; freeze schemas late.

################################################################################
# 5. SYSTEM ARCHITECTURE
################################################################################

Final architecture:

  [Surface Adapters]
    CLI
    Benchmark Runner
    CI Adapter
    PR Adapter
    IDE Adapter
        |
        v
  [Controller / Orchestrator]
    budgets
    retries
    role scheduling
    checkpoints
    artifact passing
    stop conditions
        |
        +-------------------------+
        |                         |
        v                         v
  [Model Adapter]          [Verification Core]
    CodexExecAdapter         intake normalization
    later CodexSdkAdapter    staged patching
                              task oracle runner
                              pytest runner
                              coverage/lint/type runner
                              scope guard
                              git safety
                              contracts / icontract
                              CrossHair
                              Hypothesis
                              optional mutation testing
                              ledgers / proof cards / reports
        |                         |
        +-------------+-----------+
                      |
                      v
                [Evidence Store]
                  runs
                  ledgers
                  benchmark results
                  retry transcripts
                  patch artifacts
                  reports

Runtime boundary rules:
  - No role owns verification logic.
  - No role owns git safety.
  - No role certifies correctness.
  - Roles call stable services.
  - VerificationCore is the source of truth.
  - ModelAdapter is replaceable.
  - SurfaceAdapters depend on Controller; never the reverse.

Hackathon shortcut:
  Build the first complete version in Python.
  Preserve clean module boundaries.
  Add other runtimes only if time remains and the core already works.

################################################################################
# 6. ROLE MODEL
################################################################################

Final role graph:
  - Planner
  - Coder
  - Deterministic Verifier
  - Reviewer
  - Explorer/Subagent pool
  - Controller

Important correction:
  Deterministic verification is the real verifier.
  Any LLM-based verifier is only an auditor/explainer layered on top.

Role definitions:

  Planner:
    - narrows scope
    - defines milestones
    - proposes allowed files
    - defines required checks
    - records assumptions and doubt points

  Coder:
    - proposes minimal patch
    - updates only allowed scope
    - returns patch summary
    - revises implementation after evidence feedback

  Deterministic Verifier:
    - runs task oracle
    - runs pytest/test_script
    - runs lint/type/coverage where applicable
    - runs contracts/CrossHair/Hypothesis on Python subset
    - emits VERIFIED / FALSIFIED / UNPROVEN
    - captures counterexamples and retry evidence
    - flags unsafe claims automatically

  Reviewer:
    - summarizes change and risk
    - interprets evidence
    - recommends APPROVE / NEEDS_CHANGES / UNSAFE

  Explorer/Subagent pool:
    - optional late-phase codebase exploration
    - optional test discovery
    - optional alternative patch hypothesis generation

  Controller:
    - starts runs
    - invokes model adapter
    - invokes verification core
    - decides retry / stop / escalate
    - enforces budgets
    - emits final result

Iterative layering order:
  1. Coder only
  2. Coder + deterministic verifier
  3. Coder + deterministic verifier + plan artifact
  4. Planner as separate role if useful
  5. Reviewer as evidence summarizer
  6. Additional roles only if they improve outcomes or clarity

################################################################################
# 7. REQUIRED ARTIFACTS
################################################################################

Phase-0 minimum documents:
  - README.md only
    containing:
      - baseline definition
      - treatment definition
      - first working milestone
      - first command path
      - golden task choice

Documents added after the first real working wrapper exists:
  - SPEC.md
  - PLAN.md
  - RUNBOOK.md
  - STATUS.md
  - BENCHMARK_PLAN.md

Required artifacts introduced progressively:
  - RunLedger
  - VerificationReport
  - RetryTranscript
  - ProofCard
  - BenchmarkTaskResult
  - BenchmarkComparison
  - Prose Spec Summary
  - Contract Graph
  - Failure Mode Ledger
  - Verification Ledger
  - ReviewReport (later)
  - MergeGateVerdict (later)

Tri-state verification:
  - VERIFIED
  - FALSIFIED
  - UNPROVEN

Artifact rule:
  Artifacts are discovered by running code, then stabilized.
  Do not over-design schemas before the first real wrapper run.

################################################################################
# 8. BENCHMARK CONTRACT
################################################################################

Two systems only:
  A. Baseline = Vanilla Codex
  B. Treatment = Codex + verification-first harness

Fairness rules:
  - same model
  - same repo snapshot
  - same task description
  - same environment/container
  - same timeout
  - same task subset
  - same initial working tree state
  - only the harness behavior changes

Baseline definition:
  - codex exec
  - minimal task prompt
  - no mandatory external verifier gate
  - no external retry-with-evidence loop
  - no required proof artifact

Treatment definition:
  - codex wrapper
  - intercept claimed completion
  - run task oracle / tests / checks
  - if fail, re-prompt with concrete evidence
  - bounded retries
  - emit proof artifacts and honest verdict

Benchmark ladder:
  - tiny A/B checkpoint first
  - curated subset next
  - richer subset later
  - full integration only after the core is stable

Benchmark sources:
  Preferred:
    - Harbor / Terminal-Bench curated subset
  Fallback:
    - local curated oracle tasks with reproducible validators
  Absolute fallback:
    - 3-10 reproducible repo tasks with shell/python oracles

Critical metrics:
  - Verified Success Rate
  - Unsafe Claim Rate
  - Time to Verified Success
  - Retry Count
  - Optional: Scope Violation Rate

Critical metric definition:
  Unsafe Claim Rate =
    agent signals completion/success, but oracle or required checks fail

Benchmark rule:
  Benchmark early in a tiny way, then benchmark again as features are added.

################################################################################
# 9. TECH STACK
################################################################################

Primary language:
  Python 3.11+

Core Python libraries:
  - pydantic
  - typer
  - rich
  - tenacity
  - orjson
  - asyncio / anyio
  - pathlib
  - subprocess
  - jinja2
  - httpx
  - fastapi
  - uvicorn
  - sqlite3 or sqlmodel
  - pandas
  - duckdb
  - pyarrow
  - matplotlib

Verification libraries:
  - pytest
  - pytest-xdist
  - coverage
  - hypothesis
  - icontract
  - crosshair-tool
  - ruff
  - mypy or pyright
  - junitparser
  - pathspec
  - optional later: mutmut or cosmic-ray
  - optional later: semgrep
  - optional later: tree-sitter

Codex integration:
  Early:
    - codex exec --json
    - codex exec resume
  Later:
    - Codex SDK / App Server
    - subagents
    - richer clients

Tooling rule:
  Only introduce a new toolchain when the current phase is already working.

################################################################################
# 10. REPO LAYOUT
################################################################################

correct-by-construction/
├── README.md
├── SPEC.md                    # added after Phase 1 reveals the right shape
├── PLAN.md                    # added after Phase 1
├── RUNBOOK.md                 # added after Phase 1
├── STATUS.md                  # added after Phase 1
├── BENCHMARK_PLAN.md          # added after Phase 1.5
├── pyproject.toml
├── prompts/
│   ├── planner.md
│   ├── coder.md
│   ├── verifier_auditor.md
│   ├── reviewer.md
│   └── shared_rules.md
├── src/cbc/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── controller/
│   │   ├── orchestrator.py
│   │   ├── budgets.py
│   │   ├── retries.py
│   │   ├── checkpoints.py
│   │   └── artifact_flow.py
│   ├── model/
│   │   ├── adapter.py
│   │   ├── codex_exec.py
│   │   ├── codex_sdk.py
│   │   ├── prompts.py
│   │   └── events.py
│   ├── intake/
│   │   ├── normalize.py
│   │   ├── stacktrace.py
│   │   ├── tests.py
│   │   ├── diff.py
│   │   └── bugreport.py
│   ├── workspace/
│   │   ├── staging.py
│   │   ├── worktrees.py
│   │   ├── patching.py
│   │   ├── scope_guard.py
│   │   └── git_safety.py
│   ├── verify/
│   │   ├── core.py
│   │   ├── oracle_runner.py
│   │   ├── pytest_runner.py
│   │   ├── coverage_runner.py
│   │   ├── lint_runner.py
│   │   ├── type_runner.py
│   │   ├── contracts.py
│   │   ├── contract_ir.py
│   │   ├── crosshair_runner.py
│   │   ├── hypothesis_runner.py
│   │   ├── mutation_runner.py
│   │   ├── failure_modes.py
│   │   ├── ledgers.py
│   │   └── policies.py
│   ├── roles/
│   │   ├── planner.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   ├── explorer.py
│   │   └── verifier_auditor.py
│   ├── graph/
│   │   ├── slicer.py
│   │   ├── callgraph.py
│   │   ├── dependency_dag.py
│   │   └── mismatch.py
│   ├── benchmark/
│   │   ├── baseline.py
│   │   ├── treatment.py
│   │   ├── harbor_runner.py
│   │   ├── local_runner.py
│   │   ├── metrics.py
│   │   ├── compare.py
│   │   └── reports.py
│   ├── review/
│   │   ├── summarize.py
│   │   ├── risk.py
│   │   ├── pr_comment.py
│   │   └── merge_gate.py
│   ├── api/
│   │   ├── app.py
│   │   ├── routes.py
│   │   └── streams.py
│   └── storage/
│       ├── db.py
│       ├── runs.py
│       ├── ledgers.py
│       ├── benchmark_results.py
│       └── artifacts.py
├── fixtures/
│   ├── golden_debug/
│   ├── golden_review/
│   ├── curated_subset/
│   └── oracle_tasks/
├── scripts/
│   ├── run_baseline.sh
│   ├── run_treatment.sh
│   ├── run_compare.sh
│   ├── render_proof_card.py
│   └── export_demo_bundle.py
├── artifacts/
├── reports/
├── benchmark-configs/
│   ├── baseline.yaml
│   ├── treatment.yaml
│   └── curated_subset.yaml
└── jetbrains-plugin/   # later only

Repo rule:
  Each new phase adds modules and artifacts.
  It should not require reshaping the entire tree.

################################################################################
# 11. MULTI-PHASE PLAN — BUILT LIKE A CORRECT BIKE
################################################################################

===============================================================================
PHASE 0 — BOOTSTRAP, NOT BUREAUCRACY
===============================================================================

Timebox:
  30–45 minutes maximum

Goal:
  Make Phase 1 possible immediately.

Only do:
  - create repo skeleton
  - define baseline vs treatment in 5–10 lines inside README.md
  - choose one golden task
  - add stub model adapter
  - add stub verifier entrypoint
  - add one README with:
      - what baseline is
      - what treatment is
      - what the first working milestone is
      - the single command path you are about to implement

Do not do yet:
  - full SPEC.md
  - full BENCHMARK_PLAN.md
  - full RUNBOOK.md
  - finalized schemas
  - final proof-card format
  - elaborate artifact taxonomy

What exists at the end:
  The frame is standing and coding starts immediately.

What is proven:
  Nothing except that the team is aligned enough to begin real work.

Phase gate:
  - repo skeleton exists
  - baseline/treatment definition written
  - golden task chosen
  - stub adapter and stub verifier entrypoint present
  - coding on the wrapper starts immediately after this phase

===============================================================================
PHASE 1 — THE FIRST ROLLING BIKE
===============================================================================

Goal:
  Build the smallest truthful working system.

Meaning:
  Implement the real product core:
    Codex -> oracle -> retry -> verdict -> proof card

Scope:
  - invoke Codex
  - intercept claimed completion
  - run deterministic oracle
  - retry with concrete failure evidence
  - bounded retries
  - staged/temp workspace
  - RunLedger + RetryTranscript + ProofCard
  - rich terminal UI
  - unsafe claim detection

Implementation details:
  - start with shell/python tasks and simple repo fixtures
  - define oracle per task:
      test_script.sh
      pytest path
      command exit code
      local validator
  - track:
      model output
      claimed success
      oracle pass/fail
      retry evidence
      final verdict

What exists at the end:
  A tiny truthful product.

What is proven:
  The core loop works.

Phase gate:
  - one golden task works end-to-end
  - unsafe claims are detectable
  - proof card renders
  - no unsafe working-tree mutation
  - first real artifacts exist; these reveal the correct schema shapes

Post-phase action:
  Now create SPEC.md / PLAN.md / RUNBOOK.md / STATUS.md based on the real
  outputs from Phase 1, not speculation from before it.

===============================================================================
PHASE 1.5 — THE FIRST TEST RIDE
===============================================================================

Goal:
  Confirm the tiny bike actually beats walking.

Meaning:
  Run tiny A/B checkpoint on 2–4 tasks.

Scope:
  - baseline vs treatment
  - record metrics
  - measure Unsafe Claim Rate
  - identify first golden tasks
  - create BENCHMARK_PLAN.md from real results

What exists at the end:
  The first evidence that the harness matters.

What is proven:
  The approach is not just elegant — it helps.

Phase gate:
  - treatment wins on at least one meaningful metric
  - fairness story is clean
  - first chart exists
  - BENCHMARK_PLAN.md is written from observed reality

===============================================================================
PHASE 2 — FILE-BACKED LOOP ON REAL TERRAIN
===============================================================================

Goal:
  Make the bike useful on real terrain.

Meaning:
  Move to file-backed staged patch/test/retry loop.

Scope:
  - file-path intake
  - patch application
  - pytest/test script execution
  - scope guard
  - git safety
  - real repo-safe retry flow

Verification order:
  1. task oracle
  2. pytest / test script
  3. lint / type if cheap
  4. deeper proof extras only if applicable

What exists at the end:
  The same core loop, now on real files.

What is proven:
  The system works beyond toy inputs.

Phase gate:
  - one real file-backed bug fixed safely
  - baseline and treatment both run on same snapshot
  - unsafe claims still measured
  - previous Phase-1 golden task still works unchanged

===============================================================================
PHASE 3 — DEEPER VERIFICATION WHERE IT EARNS ITS KEEP
===============================================================================

Goal:
  Add deeper verification only where it genuinely helps.

Meaning:
  Add Python-specific proof power:
    contracts, CrossHair, Hypothesis, failure-mode artifacts

Scope:
  - Prose Spec Summary
  - Contract Graph
  - Failure Mode Ledger
  - Verification Ledger
  - icontract
  - CrossHair
  - Hypothesis
  - enhanced proof ledger

Rule:
  This phase must not block non-Python or oracle-backed tasks.

What exists at the end:
  The core loop plus deeper reasoning on selected tasks.

What is proven:
  The system can do more than re-run tests on Python-friendly logic.

Phase gate:
  - at least one Python task gains value from deeper verification
  - no non-Python task is blocked by this layer
  - baseline/treatment compare still works

===============================================================================
PHASE 4 — CURATED BENCHMARK DASHBOARD
===============================================================================

Goal:
  Turn working behavior into visible benchmark evidence.

Meaning:
  Build the curated benchmark harness.

Scope:
  - curated 5–10 task subset
  - compare runner
  - benchmark reports
  - scoreboard chart
  - 3 golden tasks frozen

Execution modes:
  Preferred:
    Harbor / Terminal-Bench subset

  Fallback:
    local curated oracle tasks with reproducible validators

What exists at the end:
  Reproducible benchmark story.

What is proven:
  The product improves verified outcomes on a fair curated subset.

Phase gate:
  - one command runs curated comparison
  - treatment has defendable win
  - golden demo tasks are frozen
  - Phase 1 and Phase 2 flows still work

===============================================================================
PHASE 5 — PLAN ARTIFACT FIRST, PLANNER ROLE SECOND
===============================================================================

Goal:
  Add guidance without turning planning into theater.

Meaning:
  Add plan artifact first; separate Planner role only if useful.

Scope:
  Stage A:
    - mandatory plan artifact
    - allowed files
    - required checks
    - doubt points
  Stage B:
    - separate Planner invocation only if it helps outcomes or clarity

What exists at the end:
  Better control and reduced sprawl.

What is proven:
  Planning improves execution instead of just adding latency.

Phase gate:
  - every run has a plan artifact
  - plan reduces sprawl or improves clarity
  - separate Planner only survives if it earns its keep
  - previous benchmark subset still compares cleanly

===============================================================================
PHASE 6 — REVIEW / DIFF / CI EXTENSION
===============================================================================

Goal:
  Carry more use cases using the same frame.

Meaning:
  Extend same verification core into review and CI.

Scope:
  - diff ingestion
  - targeted validation
  - risk summary
  - review artifact
  - CI artifact

What exists at the end:
  The same system now supports debug + review.

What is proven:
  The architecture generalizes without rewriting the core loop.

Phase gate:
  - review mode uses same verifier
  - no duplicated trust logic
  - concise review artifacts work
  - debug path still works unchanged

===============================================================================
PHASE 7 — BOUNDED STRUCTURAL REASONING
===============================================================================

Goal:
  Expand from local trust to bounded structural trust.

Meaning:
  Add multi-function slice reasoning and dependency graph checks.

Scope:
  - dependency slicer
  - DAG
  - contract mismatch checks
  - bounded global-safety reasoning

What exists at the end:
  The bike handles more complex terrain.

What is proven:
  The system can detect locally-valid but globally-unsafe changes.

Phase gate:
  - one bounded multi-function case works
  - no explosion into whole-repo proving
  - prior phases remain intact

===============================================================================
PHASE 8 — TEST GROWTH AND EDGE-CASE DISCOVERY
===============================================================================

Goal:
  Make the system improve test quality too.

Meaning:
  Add regression test generation and edge-case discovery.

Scope:
  - test gap detection
  - regression tests
  - Hypothesis strategies
  - counterexample-to-test path
  - optional bounded mutation testing

What exists at the end:
  The system not only checks fixes, it strengthens future trust.

What is proven:
  The harness improves the verification environment itself.

Phase gate:
  - at least one useful new test artifact generated
  - evidence quality improves
  - prior benchmark behavior is not harmed

===============================================================================
PHASE 9 — MULTI-ROLE GEARBOX
===============================================================================

Goal:
  Add richer orchestration only after the core bike works well.

Meaning:
  Add bounded multi-role and subagent behavior.

Scope:
  - explorer worker
  - alternative patch worker
  - risk-analysis worker
  - role scheduler
  - artifact flow
  - budget manager

Parallelism policy:
  Parallelize only:
    - exploration
    - test discovery
    - risk analysis
    - alternative hypotheses

  Do not parallelize:
    - unrestricted editing of same files
    - overlapping retries without isolation
    - anything that confuses evidence ownership

What exists at the end:
  More sophisticated control without losing truth.

What is proven:
  Extra roles improve results or clarity.
  If not, keep the simpler sequential loop.

Phase gate:
  - at least two specialized roles earn their cost
  - no truth logic moves into role chatter
  - simple sequential loop still available as fallback

===============================================================================
PHASE 10 — IDE / PRODUCT SHELL
===============================================================================

Goal:
  Make the system easier to use without touching the trust core.

Meaning:
  Add IDE shell and polish.

Scope:
  - JetBrains tool window
  - artifact viewer
  - benchmark tab
  - thin backend bridge

What exists at the end:
  Better adoption surface.

What is proven:
  Surfaces can change without changing trust logic.

Phase gate:
  - CLI and IDE produce same underlying results
  - IDE only visualizes and controls, does not redefine truth
  - core benchmark loop still works headless

################################################################################
# 12. MASTER RULE FOR EVERY PHASE
################################################################################

At the end of every phase, all of the following must be true:

1. The previous working loop still works.
2. The new capability is real, not just scaffolded.
3. There is one reproducible command path.
4. There is one checked-in artifact example.
5. There is one short demo flow.
6. STATUS.md is updated if STATUS.md exists for that phase.
7. PLAN.md is updated if assumptions changed.
8. Mini-benchmark or benchmark is rerun if the phase can affect outcomes.

If these are not true, the phase is not complete.

################################################################################
# 13. CUT LINES IF TIME COLLAPSES
################################################################################

Cut first:
  1. mutation testing
  2. CrossHair if unstable
  3. JetBrains plugin
  4. separate Planner role
  5. Reviewer role
  6. subagents
  7. multi-function graph

Never cut:
  1. baseline vs treatment fairness
  2. oracle-backed retry loop
  3. proof artifacts
  4. Unsafe Claim Rate measurement
  5. golden demo tasks
  6. scoreboard
  7. the rule that each phase must leave a working system

################################################################################
# 14. HACKATHON EXECUTION ORDER
################################################################################

First 45 minutes:
  - Phase 0 only
  - repo skeleton
  - baseline/treatment definition
  - golden task selected
  - stub adapter and verifier entrypoint

Hours 1-8:
  - Phase 1
  - real wrapper
  - oracle runner
  - retry-with-evidence
  - proof card
  - rich terminal output

Hours 8-10:
  - write SPEC.md / PLAN.md / RUNBOOK.md / STATUS.md from the real working loop

Hours 10-13:
  - Phase 1.5
  - tiny A/B
  - first chart
  - first golden task shortlist
  - BENCHMARK_PLAN.md written

Hours 13-18:
  - Phase 2
  - file-backed staged patching
  - scope guard
  - git safety
  - real repo task

Hours 18-22:
  - Phase 4 curated benchmark subset
  - scoreboard
  - freeze 3 golden tasks

Hours 22-24:
  - README cleanup
  - proof cards
  - dry run

If ahead:
  - Phase 3 Python proof enhancements
  - Phase 5 plan artifact
  - light review mode

If behind:
  Stop after Phase 2 or Phase 4.
  That is still a strong project.

################################################################################
# 15. MASTER CODING AGENT INSTRUCTION
################################################################################

You are building "Correct by Construction", a verification-first Codex harness.

Build it using a correct-by-construction development method:

- start with the smallest truthful working system
- prove it works
- measure it
- add exactly one meaningful capability
- prove it still works
- measure again
- repeat

Do not build speculative infrastructure that does not serve the current working
phase. Do not add a new layer if the previous layer is not stable.

Your core job:
  Build a system that measurably improves verified outcomes over Vanilla Codex
  on the same tasks, with the same model, same timeout, same environment, and
  the same starting repo state.

Hard constraints:
1. Proposal != trust.
2. Deterministic verification is the source of truth.
3. Retry-with-evidence is the product core.
4. Baseline vs treatment fairness must be preserved.
5. Each phase = previous working system + one new capability.
6. Never break the previous working loop.
7. Use staged workspaces and strict git safety.
8. Emit honest VERIFIED / FALSIFIED / UNPROVEN verdicts.
9. Measure Unsafe Claim Rate from the beginning.
10. Save artifacts at every phase.
11. Prefer layering over rewrites.
12. Keep future extensibility, but do not overbuild early.
13. Freeze behavior early; freeze schemas late.
14. Phase 0 must be timeboxed to 30–45 minutes.

Build in this exact iterative order unless blocked:

PHASE 0
- Create repo skeleton.
- Add README.md only.
- In README.md define:
    - baseline
    - treatment
    - first working milestone
    - first command path
    - golden task
- Add stub model adapter.
- Add stub verifier entrypoint.
- Do not design finalized schemas yet.
- Do not write full SPEC/RUNBOOK/BENCHMARK docs yet.

PHASE 1
- Implement minimal Codex wrapper using codex exec --json.
- Intercept claimed completion.
- Run deterministic oracle.
- Retry with concrete failure evidence.
- Emit first real run artifacts:
    - RunLedger
    - RetryTranscript
    - VerificationReport
    - ProofCard
- Render rich terminal output.
- Keep everything in staged/temp workspaces.
- Let real runs reveal the correct artifact shapes.

AFTER PHASE 1
- Create SPEC.md, PLAN.md, RUNBOOK.md, STATUS.md from the observed Phase-1
  behavior and artifacts.
- Stabilize schemas only after seeing real runs.

PHASE 1.5
- Run 2–4 task A/B comparison.
- Implement Verified Success Rate and Unsafe Claim Rate.
- Save first compare report and first chart.
- Freeze initial golden tasks.
- Create BENCHMARK_PLAN.md from actual observed benchmark behavior.

PHASE 2
- Add file-backed staged patching.
- Add scope guard and git safety.
- Add pytest/test-script execution on real repo tasks.
- Keep compare harness working continuously.

PHASE 3
- Add Python-specific deeper verification:
  Prose Spec Summary, Contract Graph, Failure Mode Ledger, Verification Ledger,
  icontract, CrossHair, Hypothesis.
- Never let this block oracle-backed tasks.

PHASE 4
- Add curated benchmark subset runner.
- Produce scoreboard, reports, and artifact bundles.
- Freeze 3 golden demo tasks.

PHASE 5
- Add mandatory plan artifact.
- Split Planner into a separate role only if it measurably helps.

PHASE 6
- Add review/diff/CI outputs using same verification core.

PHASE 7
- Add bounded dependency graph / multi-function slice checks.

PHASE 8
- Add test generation and edge-case discovery.

PHASE 9
- Add bounded multi-role/subagent orchestration only if it improves outcomes.

PHASE 10
- Add thin IDE surface last.

Implementation rules:
- Python 3.11+, typed models, small composable modules.
- Keep ModelAdapter, VerificationCore, WorkspaceManager, BenchmarkRunner,
  EvidenceStore, and SurfaceAdapters decoupled.
- No role owns validators, proof logic, or git safety.
- After every phase:
    - run validation
    - save artifact examples
    - update STATUS.md if it exists
    - update PLAN.md if assumptions changed
    - rerun mini-benchmark if relevant
- Never introduce a second runtime unless clearly justified.

Definition of success:
- At every point in development, the project remains a working truthful system.
- At demo time, we have a reproducible comparison where Vanilla Codex and our
  harness run the same tasks and our harness shows stronger verified outcomes or
  lower unsafe claim rate.
- The final product feels like a natural growth of the first tiny working loop,
  not a rewrite.

################################################################################
# 16. DEFINITION OF DONE
################################################################################

Hackathon done-enough:
  - the smallest working loop exists
  - that loop has been benchmarked
  - that loop has been strengthened iteratively
  - benchmark chart exists
  - proof card exists
  - golden demo tasks exist
  - one live task exists
  - story is coherent in under 3 minutes

Long-term done-enough:
  - the final system is visibly the layered evolution of the first truthful loop
  - debug/review/CI/IDE all reuse the same verification core
  - richer features were added without breaking the original invariants
  - the product and the development method both embody "correct by construction"
