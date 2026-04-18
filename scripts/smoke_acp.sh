#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src ./.venv/bin/python -c "import axiom.agent; print('Axiom ACP agent import ok')"
