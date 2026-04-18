#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

"$SCRIPT_DIR/run_baseline.sh"
"$SCRIPT_DIR/run_treatment.sh"

python3 "$SCRIPT_DIR/compare_suite_reports.py" \
  --baseline "$REPO_ROOT/reports/baseline-smoke/suite-summary.json" \
  --treatment "$REPO_ROOT/reports/treatment-smoke/suite-summary.json" \
  --json-output "$REPO_ROOT/reports/compare/compare.json" \
  --markdown-output "$REPO_ROOT/reports/compare/compare.md"
