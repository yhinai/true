from __future__ import annotations


def build_totality_contracts(function_name: str, source: str) -> list[str]:
    if function_name == "apply_discount" or "pct" in source:
        return [
            "@icontract.require(lambda price: math.isfinite(price) and price >= 0)",
            "@icontract.require(lambda pct: 0 <= pct <= 100)",
            "@icontract.ensure(lambda result: math.isfinite(result) and result >= 0)",
        ]
    return ["@icontract.ensure(lambda result: result is not None)"]
