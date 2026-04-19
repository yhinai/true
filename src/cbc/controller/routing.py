"""Decide what to do after a verification step."""

from __future__ import annotations

from enum import Enum

from cbc.controller.run_state import RunState
from cbc.models import VerificationVerdict


class RouteDecision(str, Enum):
    RETRY = "retry"
    COMPLETE = "complete"
    ABORT = "abort"


def route_after_verify(state: RunState) -> RouteDecision:
    if not state.iteration_history:
        return RouteDecision.ABORT
    latest = state.iteration_history[-1]
    if latest.verdict is VerificationVerdict.VERIFIED:
        return RouteDecision.COMPLETE
    if state.iteration >= state.max_iterations:
        return RouteDecision.ABORT
    return RouteDecision.RETRY
