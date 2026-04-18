from axiom.schema import AxiomName, BugClassification, VerificationOutcome, VerificationStatus


def test_bug_classification_validation() -> None:
    model = BugClassification(
        axiom=AxiomName.TOTALITY,
        confidence=0.9,
        rationale="Missing bounds.",
        target_function="apply_discount",
        bug_summary="Can go negative.",
    )
    assert model.axiom == AxiomName.TOTALITY


def test_verification_outcome_status() -> None:
    outcome = VerificationOutcome(
        status=VerificationStatus.UNPROVEN,
        raw_output="timeout",
        command=["python", "-m", "crosshair"],
    )
    assert outcome.status is VerificationStatus.UNPROVEN
