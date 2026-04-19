# Proof Card

- Run ID: `example-slugify-property-regression-treatment`
- Task: `slugify_property_regression`
- Mode: `treatment`
- Verdict: `VERIFIED`
- Attempts: `2`
- Unsafe claims: `1`

## Summary
All deterministic checks passed. Source workspace <repo>/fixtures/oracle_tasks/slugify_property_regression/workspace was copied into staged workspace <staged_workspace>. All edits are confined to the staged copy. Checkpoints: attempt-1@workspace, attempt-2@workspace.

## Proof Points
- deterministic_verdict=VERIFIED
- unsafe_claims=1
- adapter=replay
- controller_mode=sequential
- workspace_isolation=<staged_workspace>
- total_tokens=0
- explorer_targets=slugify.py
- explorer_tests=test_slugify.py
- generated_regression_test=artifacts/examples/slugify_property_regression_treatment/generated_tests/test_slugify_property_regression.py
- counterexample_artifact=artifacts/examples/slugify_property_regression_treatment/counterexamples/slugify_counterexample.json
