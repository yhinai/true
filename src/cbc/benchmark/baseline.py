from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cbc.benchmark.replay import run_task as run_replay_task
from cbc.benchmark.types import BenchmarkTaskResult as ReplayBenchmarkTaskResult
from cbc.benchmark.types import TaskDefinition
from cbc.config import AppConfig
from cbc.controller.orchestrator import run_task
from cbc.models import BenchmarkTaskResult, TaskSpec
from cbc.storage.artifacts import write_markdown


def run_baseline(task: TaskSpec, config: AppConfig) -> BenchmarkTaskResult:
    ledger = run_task(task, mode="baseline", config=config)
    return BenchmarkTaskResult(
        task_id=task.task_id,
        mode="baseline",
        verdict=ledger.verdict,
        verified_success=ledger.verdict.value == "VERIFIED",
        unsafe_claims=ledger.unsafe_claims,
        retries=max(len(ledger.attempts) - 1, 0),
        elapsed_seconds=ledger.elapsed_seconds,
        total_tokens=ledger.total_tokens,
        estimated_cost_usd=ledger.estimated_cost_usd,
        artifact_dir=ledger.artifact_dir,
    )


def run_baseline_suite(
    tasks: Iterable[TaskDefinition],
    *,
    timeout_s: int = 30,
    artifact_dir: Path | None = None,
) -> list[ReplayBenchmarkTaskResult]:
    results: list[ReplayBenchmarkTaskResult] = []
    for task in tasks:
        task_dir = artifact_dir / "tasks" / task.task_id if artifact_dir else None
        result = run_replay_task(
            task=task,
            mode="baseline",
            max_retries=0,
            timeout_s=timeout_s,
            artifact_dir=task_dir,
        )
        if task_dir is not None:
            verification = {
                "task_id": task.task_id,
                "title": task.title,
                "mode": "baseline",
                "verified": result.verified,
                "unsafe_claim": result.unsafe_claim,
                "attempt_count": result.attempt_count,
                "retries_used": result.retries_used,
                "duration_s": result.duration_s,
                "ledger_path": result.ledger_path,
                "proof_card_path": result.proof_card_path,
            }
            (task_dir / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
            write_markdown(
                task_dir / "proof-card.md",
                "\n".join(
                    [
                        f"# Proof Card: {task.task_id}",
                        "",
                        f"- Verdict: `{'PASS' if result.verified else 'FAIL'}`",
                        f"- Mode: `baseline`",
                        f"- Attempts: `{result.attempt_count}`",
                        f"- Unsafe claim: `{result.unsafe_claim}`",
                        "",
                        result.proof_card.summary,
                        "",
                    ]
                ),
            )
        results.append(result)
    return results
