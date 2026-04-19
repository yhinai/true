#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
uv run --extra dev cbc controller-compare --config-path benchmark-configs/controller_subset.yaml "$@"
