from __future__ import annotations


def build_non_contradiction_contracts(function_name: str, source: str) -> list[str]:
    if function_name == "build_checkout_state" or ("is_loading" in source and "error" in source):
        return [
            "@icontract.ensure(lambda result: (not result[0]) or (result[1] is None))",
        ]
    return ["@icontract.ensure(lambda result: result is not None)"]
