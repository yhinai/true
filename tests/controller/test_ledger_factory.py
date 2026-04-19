from datetime import datetime
from pathlib import Path

from cbc.controller.ledger_factory import build_final_ledger
from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import (
    AttemptRecord,
    CheckResult,
    CheckStatus,
    ModelResponse,
    PlanArtifact,
    ProofCard,
    RunLedger,
    VerificationReport,
    VerificationVerdict,
)


def _state_verified() -> RunState:
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    state.iteration = 1
    state.record_iteration(
        IterationRecord(
            iteration=1,
            verdict=VerificationVerdict.VERIFIED,
            files_modified=[Path("a.py")],
        )
    )
    state.completed_at = datetime(2026, 1, 1, 0, 1)
    return state


def _verification() -> VerificationReport:
    return VerificationReport(
        verdict=VerificationVerdict.VERIFIED,
        checks=[
            CheckResult(
                name="oracle",
                command="true",
                status=CheckStatus.PASSED,
            )
        ],
        summary="all checks passed",
    )


def test_build_final_ledger_returns_run_ledger():
    state = _state_verified()
    verification = _verification()
    attempt = AttemptRecord(
        attempt=1,
        prompt="do the thing",
        model_response=ModelResponse(summary="ok"),
        verification=verification,
    )
    plan = PlanArtifact(
        summary="minimal plan",
        allowed_files=["a.py"],
        required_checks=["oracle"],
        doubt_points=[],
    )
    proof = ProofCard(
        run_id="run-1",
        task_id="t1",
        mode="treatment",
        verdict=VerificationVerdict.VERIFIED,
        unsafe_claims=0,
        attempts=1,
        summary="verified",
        proof_points=["deterministic_verdict=VERIFIED"],
        artifact_dir=Path("/tmp/art"),
    )

    ledger = build_final_ledger(
        state=state,
        attempts=[attempt],
        final_verification=verification,
        proof_card=proof,
        run_id="run-1",
        title="Task One",
        mode="treatment",
        controller_mode="sequential",
        selected_candidate_id=None,
        adapter="replay",
        artifact_dir=Path("/tmp/art"),
        workspace_dir=Path("/tmp/ws"),
        plan=plan,
        candidate_results=[],
        unsafe_claims=0,
        model_calls_used=1,
        final_summary="verified and done",
    )
    assert isinstance(ledger, RunLedger)
    assert ledger.task_id == "t1"
    assert ledger.run_id == "run-1"
    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert ledger.started_at == datetime(2026, 1, 1)
    assert ledger.ended_at == datetime(2026, 1, 1, 0, 1)
    assert ledger.final_summary == "verified and done"
    assert ledger.attempts == [attempt]
