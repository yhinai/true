from __future__ import annotations


def infer_required_checks(oracles: list[str]) -> list[str]:
    return oracles or ["oracle"]
