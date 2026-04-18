# Demo Script

1. Show `demo_repo/tests/test_discount.py` failing against the original function.
2. Run `make demo`.
3. Point to the ledger: bug, axiom, patch, contracts, verification, tests, wall time.
4. Run `PYTHONPATH=src ./.venv/bin/python -m axiom.cli --bug demo_repo/checkout/discount.py --test demo_repo/tests/test_discount.py --verify-original`.
5. Say: "Not a guess - a witness."
6. Run `make demo` with `--force-unproven` from the CLI for the honest fallback path.

## Optional second beat

Only use these if the golden path is already stable in rehearsal:

1. Run `make demo-non-contradiction`.
2. Explain that Axiom can also detect contradictory state, not just missing bounds.
3. Run `make demo-identity`.
4. Explain that Axiom can also protect conceptual identity when distinct IDs are mixed.

Keep both optional beats short. Do not let them replace the Totality-led main demo.
