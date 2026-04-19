"""Every VerificationVerdict value must produce a valid RouteDecision."""

from __future__ import annotations

from datetime import datetime

import pytest

from cbc.controller.routing import RouteDecision, route_after_verify
from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import VerificationVerdict


@pytest.mark.parametrize(
    "verdict",
    list(VerificationVerdict),
    ids=[v.value for v in VerificationVerdict],
)
def test_verdict_has_valid_route(verdict: VerificationVerdict) -> None:
    state = RunState(task_id="auto", max_iterations=3, started_at=datetime(2026, 1, 1))
    state.iteration = 1
    state.record_iteration(IterationRecord(iteration=1, verdict=verdict))
    decision = route_after_verify(state)
    assert isinstance(decision, RouteDecision)
