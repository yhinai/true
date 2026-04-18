from __future__ import annotations

from pathlib import Path
from typing import Callable

from .replay import run_task
from .types import BenchmarkTaskResult, TaskDefinition

TaskOrchestrator = Callable[..., object]


def run_treatment_suite(
    tasks: list[TaskDefinition],
    max_retries: int = 2,
    timeout_s: int = 30,
    orchestrator: TaskOrchestrator | None = None,
    artifact_dir: Path | None = None,
) -> list[BenchmarkTaskResult]:
    results: list[BenchmarkTaskResult] = []
    for task in tasks:
        results.append(
            run_task(
                task=task,
                mode="treatment",
                max_retries=max_retries,
                timeout_s=timeout_s,
                orchestrator=orchestrator,
                artifact_dir=artifact_dir,
            )
        )
    return results

