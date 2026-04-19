from datetime import datetime
from pathlib import Path

from cbc.controller.run_state import IterationRecord, RunState
from cbc.models import VerificationVerdict


def test_run_state_initial_defaults():
    state = RunState(
        task_id="t1",
        max_iterations=3,
        started_at=datetime(2026, 1, 1),
    )
    assert state.iteration == 0
    assert state.failure_context == []
    assert state.files_modified == set()
    assert state.iteration_history == []
    assert state.completed_at is None


def test_run_state_failure_context_caps_at_10():
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    for i in range(15):
        state.append_failure(f"err{i}")
    assert len(state.failure_context) == 10
    assert state.failure_context[0] == "err5"
    assert state.failure_context[-1] == "err14"


def test_record_iteration_appends_history_and_updates_modified():
    state = RunState(task_id="t1", max_iterations=3, started_at=datetime(2026, 1, 1))
    record = IterationRecord(
        iteration=1,
        verdict=VerificationVerdict.FALSIFIED,
        files_modified=[Path("a.py"), Path("b.py")],
        error_summary="tests failed",
    )
    state.record_iteration(record)
    assert len(state.iteration_history) == 1
    assert state.iteration_history[0] is record
    assert state.files_modified == {Path("a.py"), Path("b.py")}
