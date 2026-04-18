#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="/Users/alhinai/Desktop/TRUE/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m cbc.main run /Users/alhinai/Desktop/TRUE/fixtures/oracle_tasks/calculator_bug/task.yaml --mode baseline
