#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="/Users/alhinai/Desktop/TRUE/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m cbc.main compare --config-path /Users/alhinai/Desktop/TRUE/benchmark-configs/curated_subset.yaml
