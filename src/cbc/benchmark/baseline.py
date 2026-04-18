from __future__ import annotations

from pathlib import Path
from typing import Callable

from .replay import run_task
from .types import BenchmarkTaskResult, TaskDefinition

TaskOrchestrator = Callable[..., object]


def run_baseline_suite(
    tasks: list[TaskDefinition],
    timeout_s: int = 30,
    orchestrator: TaskOrchestrator | None = None,
    artifact_dir: Path | None = None,
) -> list[BenchmarkTaskResult]:
    results: list[BenchmarkTaskResult] = []
    for task in tasks:
        results.append(
            run_task(
                task=task,
                mode="baseline",
                max_retries=0,
                timeout_s=timeout_s,
                orchestrator=orchestrator,
                artifact_dir=artifact_dir,
            )
        )
    return results

