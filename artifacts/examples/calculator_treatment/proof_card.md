# Proof Card

- Run ID: `7d73212025fb`
- Task: `calculator_bug`
- Mode: `treatment`
- Verdict: `VERIFIED`
- Attempts: `2`
- Unsafe claims: `1`

## Summary
All deterministic checks passed. Source workspace /Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/calculator_bug/workspace was copied into staged workspace /var/folders/56/k6d868zx2c755lc49bbjkt740000gn/T/cbc-workspace-6y43q1ej/workspace. All edits are confined to the staged copy. Checkpoints: attempt-1@workspace, attempt-2@workspace.

## Proof Points
- deterministic_verdict=VERIFIED
- unsafe_claims=1
- adapter=replay
- controller_mode=gearbox
- workspace_isolation=/var/folders/56/k6d868zx2c755lc49bbjkt740000gn/T/cbc-workspace-6y43q1ej/workspace
- explorer_targets=calculator.py
- explorer_tests=test_calculator.py
- selected_candidate=candidate_a
- candidate_count=2
