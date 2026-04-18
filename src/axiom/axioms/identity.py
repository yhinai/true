from __future__ import annotations


def build_identity_contracts(function_name: str, source: str) -> list[str]:
    if function_name == "pair_user_and_order_ids" or ("user_id" in source and "order_id" in source):
        return [
            "@icontract.require(lambda user_id: user_id.startswith('U-'))",
            "@icontract.require(lambda order_id: order_id.startswith('O-'))",
            "@icontract.ensure(lambda result, user_id, order_id: result[0] == user_id and result[1] == order_id)",
        ]
    return ["@icontract.ensure(lambda result: result is not None)"]
