# Scaffold Compare Report

This compare report only checks scaffold readiness on the checked-in reference solutions. It is not an agent-performance benchmark yet.

## Readiness

- Same task set: `True`
- Baseline verified success rate: `1.00`
- Treatment verified success rate: `1.00`
- Success-rate delta: `0.00`

## Policy Delta

| Setting | Baseline | Treatment |
| --- | --- | --- |
| max_attempts | 1 | 3 |
| retry_with_evidence | False | True |
| require_proof_card | False | True |
