# Proof Card

- Run ID: `14902e92a6bc`
- Task: `slugify_property_regression`
- Mode: `treatment`
- Verdict: `VERIFIED`
- Attempts: `2`
- Unsafe claims: `1`

## Summary
All deterministic checks passed. Source workspace /Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/slugify_property_regression/workspace was copied into staged workspace /var/folders/56/k6d868zx2c755lc49bbjkt740000gn/T/cbc-workspace-9rb66bc9/workspace. All edits are confined to the staged copy. Checkpoints: attempt-1@workspace, attempt-2@workspace.

## Proof Points
- deterministic_verdict=VERIFIED
- unsafe_claims=1
- adapter=replay
- controller_mode=sequential
- workspace_isolation=/var/folders/56/k6d868zx2c755lc49bbjkt740000gn/T/cbc-workspace-9rb66bc9/workspace
- explorer_targets=slugify.py
- explorer_tests=test_slugify.py
- generated_regression_test=/Users/alhinai/Desktop/TRUE/artifacts/runs/a21959f231c9/generated_tests/test_slugify_property_regression.py
- counterexample_artifact=/Users/alhinai/Desktop/TRUE/artifacts/runs/a21959f231c9/counterexamples/slugify_counterexample.json
