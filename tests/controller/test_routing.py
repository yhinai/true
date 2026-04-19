from datetime import datetime

from cbc.controller.routing import RouteDecision, route_after_verify
from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import VerificationVerdict


def _state_with_verdict(verdict: VerificationVerdict, iteration: int, max_iterations: int = 3) -> RunState:
    state = RunState(task_id="t1", max_iterations=max_iterations, started_at=datetime(2026, 1, 1))
    state.iteration = iteration
    state.record_iteration(IterationRecord(iteration=iteration, verdict=verdict))
    return state


def test_route_complete_on_verified():
    state = _state_with_verdict(VerificationVerdict.VERIFIED, iteration=1)
    assert route_after_verify(state) is RouteDecision.COMPLETE


def test_route_retry_on_falsified_under_budget():
    state = _state_with_verdict(VerificationVerdict.FALSIFIED, iteration=1, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.RETRY


def test_route_abort_when_budget_exhausted():
    state = _state_with_verdict(VerificationVerdict.FALSIFIED, iteration=3, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.ABORT


def test_route_abort_on_unproven_no_retry():
    state = _state_with_verdict(VerificationVerdict.UNPROVEN, iteration=1, max_iterations=3)
    assert route_after_verify(state) is RouteDecision.ABORT
