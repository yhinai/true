from __future__ import annotations


def compact_stacktrace(output: str, limit: int = 20) -> str:
    lines = output.strip().splitlines()
    return "\n".join(lines[-limit:])
