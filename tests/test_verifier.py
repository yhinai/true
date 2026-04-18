from axiom.verifier import CrossHairVerifier
from axiom.schema import VerificationStatus


def test_verifier_reports_verified_for_bounded_discount() -> None:
    source = """
import icontract

import math

@icontract.require(lambda price: math.isfinite(price) and price >= 0)
@icontract.require(lambda pct: 0 <= pct <= 100)
@icontract.ensure(lambda result: math.isfinite(result) and result >= 0)
def apply_discount(price: float, pct: int) -> float:
    if not math.isfinite(price) or price < 0:
        raise ValueError("price must be a finite non-negative number")
    if not 0 <= pct <= 100:
        raise ValueError("pct must be between 0 and 100")
    return price * (100 - pct) / 100
"""
    outcome = CrossHairVerifier().verify_source(source, "apply_discount")
    assert outcome.status == VerificationStatus.VERIFIED


def test_verifier_reports_falsified_for_unbounded_discount() -> None:
    source = """
import icontract

@icontract.ensure(lambda result: result >= 0)
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
"""
    outcome = CrossHairVerifier().verify_source(source, "apply_discount")
    assert outcome.status == VerificationStatus.FALSIFIED


def test_verifier_reports_unproven_on_timeout() -> None:
    source = """
import icontract

@icontract.ensure(lambda result: result >= 0)
def slow_identity(x: int) -> int:
    total = 0
    for _ in range(200000000):
        total += 1
    return x
"""
    outcome = CrossHairVerifier(timeout_seconds=0.1).verify_source(source, "slow_identity")
    assert outcome.status == VerificationStatus.UNPROVEN


def test_verifier_targets_requested_function_line_in_multi_function_source() -> None:
    source = """
import icontract

@icontract.ensure(lambda result: result > 0)
def helper(x: int) -> int:
    return x

@icontract.ensure(lambda result: result >= 0)
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
"""
    outcome = CrossHairVerifier().verify_source(source, "apply_discount")
    assert outcome.status == VerificationStatus.FALSIFIED
    assert outcome.counterexample is not None
    assert "apply_discount" in outcome.counterexample
