#!/usr/bin/env python3
"""Mirror a CBC run ledger to Supabase.

Thin wrapper around :func:`cbc.api.supabase_writer.mirror_run_ledger_path` used
by the ``cbc-remediate`` GitHub Actions workflow. No-op when Supabase env vars
are missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

from cbc.api.supabase_writer import mirror_run_ledger_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: remediate_mirror.py <run_ledger.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"ledger not found: {path}", file=sys.stderr)
        return 1
    ok = mirror_run_ledger_path(path)
    print(f"mirror_run_ledger_path -> {ok}")
    return 0 if ok else 0  # non-fatal: mirror is best-effort


if __name__ == "__main__":
    sys.exit(main(sys.argv))
