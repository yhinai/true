#!/usr/bin/env bash
set -euo pipefail

echo "Verified case"
./.venv/bin/python -m crosshair check --analysis_kind=icontract tests/fixtures/verified_subject.py

echo
echo "Falsified case"
if ./.venv/bin/python -m crosshair check --analysis_kind=icontract tests/fixtures/falsified_subject.py; then
  echo "Expected falsified case to fail"
  exit 1
fi
