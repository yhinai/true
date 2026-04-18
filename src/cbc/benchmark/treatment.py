from __future__ import annotations

from cbc.config import AppConfig
from cbc.controller.orchestrator import run_task
from cbc.models import BenchmarkTaskResult, TaskSpec


def run_treatment(task: TaskSpec, config: AppConfig) -> BenchmarkTaskResult:
    ledger = run_task(task, mode="treatment", config=config)
    return BenchmarkTaskResult(
        task_id=task.task_id,
        mode="treatment",
        verdict=ledger.verdict,
        verified_success=ledger.verdict.value == "VERIFIED",
        unsafe_claims=ledger.unsafe_claims,
        retries=max(len(ledger.attempts) - 1, 0),
        elapsed_seconds=ledger.elapsed_seconds,
        artifact_dir=ledger.artifact_dir,
    )
