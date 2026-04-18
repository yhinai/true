#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
uv run cbc compare --config-path benchmark-configs/live_codex_subset.yaml "$@"
