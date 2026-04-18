from axiom.detector import BugDetector
from axiom.patcher import PatchGenerator


def test_patcher_returns_bounded_discount_function() -> None:
    source = "def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n"
    classification = BugDetector().classify("failing test", source)
    patch = PatchGenerator().propose_patch(classification, source, "failing test")
    assert "raise ValueError" in patch.patched_source
    assert "0 <= pct <= 100" in patch.patched_source


def test_patcher_uses_classified_target_in_multi_function_source() -> None:
    source = (
        "def helper(x: int) -> int:\n"
        "    return x\n\n"
        "def apply_discount(price: float, pct: int) -> float:\n"
        "    return price * (100 - pct) / 100\n"
    )
    classification = BugDetector().classify("apply_discount failed with pct above 100", source)
    patch = PatchGenerator().propose_patch(classification, source, "failing test")
    assert "pct must be between 0 and 100" in patch.patched_source


def test_patcher_repairs_non_contradiction_bug() -> None:
    source = (
        "def build_checkout_state(is_loading: bool, error: str | None) -> tuple[bool, str | None]:\n"
        "    return is_loading, error\n"
    )
    classification = BugDetector().classify("loading and error cannot both be set", source)
    patch = PatchGenerator().propose_patch(classification, source, "failing test")
    assert "return False, error" in patch.patched_source


def test_patcher_repairs_identity_bug() -> None:
    source = (
        "def pair_user_and_order_ids(user_id: str, order_id: str) -> tuple[str, str]:\n"
        "    return user_id, user_id\n"
    )
    classification = BugDetector().classify("user_id and order_id were mixed", source)
    patch = PatchGenerator().propose_patch(classification, source, "failing test")
    assert "return user_id, order_id" in patch.patched_source
