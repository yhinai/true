#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
uv run --extra dev cbc poc --config-path benchmark-configs/poc_live_codex.yaml "$@"
