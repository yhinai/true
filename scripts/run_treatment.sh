#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

python3 "$SCRIPT_DIR/run_fixture_suite.py" \
  --config "$REPO_ROOT/benchmark-configs/treatment.yaml" \
  --output-dir "$REPO_ROOT/reports/treatment-smoke"
