# Proof Card

- Run ID: `example-calculator-treatment`
- Task: `calculator_bug`
- Mode: `treatment`
- Verdict: `VERIFIED`
- Attempts: `2`
- Unsafe claims: `1`

## Summary
All deterministic checks passed. Source workspace <repo>/fixtures/oracle_tasks/calculator_bug/workspace was copied into staged workspace <staged_workspace>. All edits are confined to the staged copy. Checkpoints: attempt-1@workspace, attempt-2@workspace.

## Proof Points
- deterministic_verdict=VERIFIED
- unsafe_claims=1
- adapter=replay
- controller_mode=gearbox
- workspace_isolation=<staged_workspace>
- explorer_targets=calculator.py
- explorer_tests=test_calculator.py
- selected_candidate=candidate_a
- candidate_count=2
