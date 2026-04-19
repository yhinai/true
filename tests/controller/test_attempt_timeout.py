import time

import pytest

from cbc.controller.orchestrator import _check_deadline
from cbc.controller.run_state import AttemptTimeout


def test_check_deadline_noop_when_budget_none():
    _check_deadline(started_at=0.0, budget=None)


def test_check_deadline_raises_after_budget_elapsed():
    started = time.monotonic() - 10.0
    with pytest.raises(AttemptTimeout) as ei:
        _check_deadline(started_at=started, budget=5.0)
    assert ei.value.elapsed >= 10.0


def test_check_deadline_silent_when_under_budget():
    started = time.monotonic() - 1.0
    _check_deadline(started_at=started, budget=5.0)
