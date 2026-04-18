from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Mapping

from .types import (
    BenchmarkTaskResult,
    ProofCard,
    RunAttempt,
    RunLedger,
    TaskDefinition,
    to_builtin,
    utc_now_iso,
)

TaskOrchestrator = Callable[..., object]


def _oracle_run(command: str, cwd: Path, timeout_s: int) -> tuple[bool, int, float, str, str]:
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    duration_s = time.perf_counter() - started
    return proc.returncode == 0, proc.returncode, duration_s, proc.stdout, proc.stderr


def _result_from_mapping(
    mapping: Mapping[str, object], task: TaskDefinition, mode: str
) -> BenchmarkTaskResult:
    verified = bool(mapping.get("verified", False))
    unsafe_claim = bool(mapping.get("unsafe_claim", False))
    attempt_count = int(mapping.get("attempt_count", 1))
    retries_used = int(mapping.get("retries_used", max(0, attempt_count - 1)))
    duration_s = float(mapping.get("duration_s", 0.0))
    now = utc_now_iso()
    ledger = RunLedger(
        task_id=task.task_id,
        mode=mode,
        started_at=now,
        finished_at=now,
        attempts=[],
    )
    proof = ProofCard(
        task_id=task.task_id,
        mode=mode,
        verdict="VERIFIED" if verified else "FALSIFIED",
        verified=verified,
        unsafe_claim=unsafe_claim,
        attempt_count=attempt_count,
        retries_used=retries_used,
        summary=str(mapping.get("summary", "External orchestrator result")),
        evidence=[str(item) for item in mapping.get("evidence", [])],
    )
    return BenchmarkTaskResult(
        task_id=task.task_id,
        mode=mode,
        verified=verified,
        unsafe_claim=unsafe_claim,
        attempt_count=attempt_count,
        retries_used=retries_used,
        duration_s=duration_s,
        ledger=ledger,
        proof_card=proof,
        ledger_path=str(mapping.get("ledger_path", "")),
        proof_card_path=str(mapping.get("proof_card_path", "")),
    )


def _coerce_external_result(result: object, task: TaskDefinition, mode: str) -> BenchmarkTaskResult:
    if isinstance(result, BenchmarkTaskResult):
        return result
    if isinstance(result, Mapping):
        return _result_from_mapping(result, task, mode)

    values = {
        "verified": bool(getattr(result, "verified", False)),
        "unsafe_claim": bool(getattr(result, "unsafe_claim", False)),
        "attempt_count": int(getattr(result, "attempt_count", 1)),
        "retries_used": int(getattr(result, "retries_used", 0)),
        "duration_s": float(getattr(result, "duration_s", 0.0)),
        "summary": str(getattr(result, "summary", "External orchestrator result")),
        "evidence": list(getattr(result, "evidence", [])),
        "ledger_path": str(getattr(result, "ledger_path", "")),
        "proof_card_path": str(getattr(result, "proof_card_path", "")),
    }
    return _result_from_mapping(values, task, mode)


def _persist_result_artifacts(result: BenchmarkTaskResult, artifact_dir: Path) -> BenchmarkTaskResult:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = artifact_dir / f"{result.task_id}_{result.mode}_ledger.json"
    proof_path = artifact_dir / f"{result.task_id}_{result.mode}_proof_card.json"
    ledger_path.write_text(json.dumps(to_builtin(result.ledger), indent=2), encoding="utf-8")
    proof_path.write_text(json.dumps(to_builtin(result.proof_card), indent=2), encoding="utf-8")
    result.ledger_path = str(ledger_path.resolve())
    result.proof_card_path = str(proof_path.resolve())
    return result


def run_replay_task(
    task: TaskDefinition,
    mode: str,
    max_retries: int,
    timeout_s: int = 30,
    artifact_dir: Path | None = None,
) -> BenchmarkTaskResult:
    replay_attempts = task.replay.get(mode, [])
    max_attempts = 1 if mode == "baseline" else max(1, max_retries + 1)
    planned_attempts = replay_attempts[:max_attempts]
    if not planned_attempts:
        msg = f"No replay attempts configured for task={task.task_id} mode={mode}"
        raise ValueError(msg)

    started_at = utc_now_iso()
    run_attempts: list[RunAttempt] = []
    verified = False
    unsafe_claim = False
    total_duration_s = 0.0
    evidence: list[str] = []

    for index, planned in enumerate(planned_attempts, start=1):
        oracle_passed, exit_code, duration_s, stdout, stderr = _oracle_run(
            task.oracle_command, Path(planned.candidate), timeout_s
        )
        total_duration_s += duration_s
        run_attempt = RunAttempt(
            attempt_index=index,
            candidate=planned.candidate,
            claimed_success=planned.claimed_success,
            oracle_passed=oracle_passed,
            oracle_exit_code=exit_code,
            duration_s=duration_s,
            stdout=stdout.strip(),
            stderr=stderr.strip(),
            note=planned.note,
        )
        run_attempts.append(run_attempt)

        if planned.claimed_success and not oracle_passed:
            unsafe_claim = True
            evidence.append(
                f"Attempt {index} claimed success but oracle exited {exit_code} for {task.task_id}."
            )

        if not oracle_passed:
            if stderr.strip():
                evidence.append(f"Attempt {index} stderr: {stderr.strip()}")
            elif stdout.strip():
                evidence.append(f"Attempt {index} stdout: {stdout.strip()}")
            continue

        verified = True
        evidence.append(f"Attempt {index} passed oracle with exit code 0.")
        break

    finished_at = utc_now_iso()
    verdict = "VERIFIED" if verified else "FALSIFIED"
    retries_used = max(0, len(run_attempts) - 1)
    summary = (
        f"{task.task_id} {mode} verified in {len(run_attempts)} attempt(s)"
        if verified
        else f"{task.task_id} {mode} failed oracle after {len(run_attempts)} attempt(s)"
    )

    result = BenchmarkTaskResult(
        task_id=task.task_id,
        mode=mode,
        verified=verified,
        unsafe_claim=unsafe_claim,
        attempt_count=len(run_attempts),
        retries_used=retries_used,
        duration_s=round(total_duration_s, 4),
        ledger=RunLedger(
            task_id=task.task_id,
            mode=mode,
            started_at=started_at,
            finished_at=finished_at,
            attempts=run_attempts,
        ),
        proof_card=ProofCard(
            task_id=task.task_id,
            mode=mode,
            verdict=verdict,
            verified=verified,
            unsafe_claim=unsafe_claim,
            attempt_count=len(run_attempts),
            retries_used=retries_used,
            summary=summary,
            evidence=evidence,
        ),
    )
    return _persist_result_artifacts(result, artifact_dir) if artifact_dir else result


def run_task(
    task: TaskDefinition,
    mode: str,
    max_retries: int,
    timeout_s: int = 30,
    orchestrator: TaskOrchestrator | None = None,
    artifact_dir: Path | None = None,
) -> BenchmarkTaskResult:
    if orchestrator is None:
        return run_replay_task(
            task=task,
            mode=mode,
            max_retries=max_retries,
            timeout_s=timeout_s,
            artifact_dir=artifact_dir,
        )

    result = orchestrator(task=task, mode=mode, max_retries=max_retries, timeout_s=timeout_s)
    coerced = _coerce_external_result(result, task, mode)
    return _persist_result_artifacts(coerced, artifact_dir) if artifact_dir else coerced

