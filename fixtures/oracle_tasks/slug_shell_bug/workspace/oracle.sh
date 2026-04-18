#!/usr/bin/env bash
set -euo pipefail
actual="$(python3 - <<'PY'
from app import render_slug
print(render_slug("Correct By Construction"))
PY
)"
test "$actual" = "correct-by-construction"
