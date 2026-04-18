#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
1. Show failing discount test.
2. Run `make demo`.
3. Show VERIFIED ledger.
4. Run `make demo-falsified` and show the concrete CrossHair witness.
5. Run `make demo-unproven` to show the honest UNPROVEN path.
6. If ACP fails live, switch to the CLI immediately and keep the ledger surface the same.
EOF
