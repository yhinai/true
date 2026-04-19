# Specification

## Product Thesis

Codex is the proposal engine, not the source of trust. Trust comes from deterministic verification, staged execution, bounded retries, and saved proof artifacts.

## Core Loop

1. Load a task spec from `fixtures/oracle_tasks/*/task.yaml` or another compatible task file.
2. Build a plan artifact with allowed files, required checks, and doubt points.
3. Optionally build a bounded explorer brief and choose a sequential or gearbox controller path.
4. Stage the task workspace into a temp copy.
5. Run either the replay adapter or the Codex CLI adapter.
6. Apply file writes inside the allowed scope.
7. Run deterministic verification.
8. If verification fails and budget remains, feed the failure evidence back into the next attempt.
9. Emit `VERIFIED`, `FALSIFIED`, or `UNPROVEN` plus artifacts.

## Trust Boundaries

- The model adapter never certifies correctness.
- Verification logic lives under `src/cbc/verify`.
- Workspace safety lives under `src/cbc/workspace`.
- Benchmarks use the same orchestrator and verifier as single runs.

## Implemented Surfaces

- CLI: `src/cbc/main.py`
- API: `src/cbc/api/app.py`
- Benchmark runner: `src/cbc/benchmark/compare.py`
- Review shell: `src/cbc/review`
- Headless-only contract: no IDE or editor-integration surface

## Artifact Contract

Each run saves:
- `run_ledger.json`
- `retry_transcript.json`
- `verification_report.json`
- `proof_card.md`
- `scheduler_trace.json`
- `risk_artifact.json`
- `candidate_artifacts/<candidate_id>/...` when gearbox mode runs

Each benchmark comparison saves:
- `comparison.json`
- `comparison.md`
- `scoreboard.png` when matplotlib is installed, otherwise a text note

## Phase Coverage

- Phase 0: repo skeleton, README, adapter entry points
- Phase 1: truthful loop, staged workspace, proof artifacts, unsafe-claim detection
- Phase 1.5: curated A/B comparison, metrics, compare report
- Phase 2: real file-backed patching, scope guard, workspace safety
- Phase 3-8: working deeper-verification, review, graph, and test-growth slices
- Phase 9: bounded gearbox mode with sequential fallback
- Phase 10: headless CLI/API/artifact completion
- live Codex execution is wired through a checked-in `adapter: codex` task spec
