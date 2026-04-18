# Architecture

- `detector.py` classifies the bug into an axiom.
- `patcher.py` produces a minimal patch, using OpenAI when available and a deterministic fallback for the demo path.
- `contracts.py` derives icontract decorators.
- `verifier.py` runs CrossHair and maps exit codes to `VERIFIED`, `FALSIFIED`, or `UNPROVEN`.
- `pipeline.py` joins the flow and emits a typed `EvidenceLedgerModel`.
- `ledger.py` renders the final card for CLI and ACP.
