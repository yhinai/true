from axiom.contracts import ContractGenerator
from axiom.detector import BugDetector


def test_contracts_match_discount_totality_bug() -> None:
    source = (
        "def apply_discount(price: float, pct: int) -> float:\n"
        "    if price < 0:\n"
        "        raise ValueError('price must be non-negative')\n"
        "    if not 0 <= pct <= 100:\n"
        "        raise ValueError('pct must be between 0 and 100')\n"
        "    return price * (100 - pct) / 100\n"
    )
    classification = BugDetector().classify("negative result", source)
    proposal = ContractGenerator().derive(classification, source)
    assert "@icontract.require(lambda pct: 0 <= pct <= 100)" in proposal.decorators


def test_contracts_attach_to_target_function_in_multi_function_source() -> None:
    source = (
        "def helper(x: int) -> int:\n"
        "    return x\n\n"
        "def apply_discount(price: float, pct: int) -> float:\n"
        "    return price * (100 - pct) / 100\n"
    )
    classification = BugDetector().classify("apply_discount produced a negative result", source)
    proposal = ContractGenerator().derive(classification, source)
    applied = ContractGenerator().apply_contracts(source, classification.target_function, proposal.decorators)
    helper_index = applied.index("def helper")
    contract_index = applied.index("@icontract.require(lambda price: math.isfinite(price) and price >= 0)")
    target_index = applied.index("def apply_discount")
    assert helper_index < contract_index < target_index


def test_contracts_match_non_contradiction_bug() -> None:
    source = (
        "def build_checkout_state(is_loading: bool, error: str | None) -> tuple[bool, str | None]:\n"
        "    return is_loading, error\n"
    )
    classification = BugDetector().classify("loading and error cannot both be set", source)
    proposal = ContractGenerator().derive(classification, source)
    assert "@icontract.ensure(lambda result: (not result[0]) or (result[1] is None))" in proposal.decorators


def test_contracts_match_identity_bug() -> None:
    source = (
        "def pair_user_and_order_ids(user_id: str, order_id: str) -> tuple[str, str]:\n"
        "    return user_id, user_id\n"
    )
    classification = BugDetector().classify("user_id and order_id were mixed", source)
    proposal = ContractGenerator().derive(classification, source)
    assert "@icontract.ensure(lambda result, user_id, order_id: result[0] == user_id and result[1] == order_id)" in proposal.decorators
