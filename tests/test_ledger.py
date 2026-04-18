from axiom.ledger import render_ledger
from axiom.schema import (
    AxiomName,
    EvidenceLedgerModel,
    TestRunResult,
    VerificationOutcome,
    VerificationStatus,
)


def test_ledger_renders_counterexample() -> None:
    ledger = EvidenceLedgerModel(
        bug_summary="apply_discount returns negative",
        axiom=AxiomName.TOTALITY,
        function_name="apply_discount(price: float, pct: int)",
        patch_summary="[+3 -1 lines]",
        patched_source="def apply_discount(...): ...",
        contracts=["@icontract.require(lambda pct: 0 <= pct <= 100)"],
        verification=VerificationOutcome(
            status=VerificationStatus.FALSIFIED,
            raw_output="counterexample",
            command=["python", "-m", "crosshair"],
            counterexample="apply_discount(price=100, pct=150)",
            violated_condition="result >= 0",
        ),
        tests=TestRunResult(command=["pytest"], passed=0, failed=1, ok=False, output="F"),
        wall_time_seconds=2.3,
        final_status=VerificationStatus.FALSIFIED,
    )
    rendered = render_ledger(ledger)
    assert "Counterexample:" in rendered
    assert "apply_discount(price=100, pct=150)" in rendered
