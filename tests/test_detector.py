from axiom.detector import BugDetector
from axiom.schema import AxiomName


def test_detector_classifies_discount_bug_as_totality() -> None:
    detector = BugDetector()
    source = "def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n"
    result = detector.classify("pct above 100 yields a negative result", source)
    assert result.axiom == AxiomName.TOTALITY
    assert result.target_function == "apply_discount"


def test_detector_prefers_function_named_in_bug_text() -> None:
    detector = BugDetector()
    source = (
        "def helper(x: int) -> int:\n"
        "    return x\n\n"
        "def apply_discount(price: float, pct: int) -> float:\n"
        "    return price * (100 - pct) / 100\n"
    )
    result = detector.classify("Traceback: apply_discount returned a negative result for pct=150", source)
    assert result.target_function == "apply_discount"


def test_detector_classifies_non_contradiction_bug() -> None:
    source = (
        "def build_checkout_state(is_loading: bool, error: str | None) -> tuple[bool, str | None]:\n"
        "    return is_loading, error\n"
    )
    result = BugDetector().classify("loading and error cannot both be set", source)
    assert result.axiom == AxiomName.NON_CONTRADICTION
    assert result.target_function == "build_checkout_state"


def test_detector_classifies_identity_bug() -> None:
    source = (
        "def pair_user_and_order_ids(user_id: str, order_id: str) -> tuple[str, str]:\n"
        "    return user_id, user_id\n"
    )
    result = BugDetector().classify("user_id and order_id were mixed into the wrong tuple", source)
    assert result.axiom == AxiomName.IDENTITY
    assert result.target_function == "pair_user_and_order_ids"
