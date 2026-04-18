from __future__ import annotations


def build_referential_integrity_contracts(function_name: str, source: str) -> list[str]:
    return ["@icontract.ensure(lambda result: result is not None)"]
