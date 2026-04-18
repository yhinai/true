#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m cbc.main run "$ROOT/fixtures/oracle_tasks/calculator_bug/task.yaml" --mode treatment
