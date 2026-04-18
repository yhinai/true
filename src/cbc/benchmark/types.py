from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class ReplayAttemptDefinition:
    candidate: str
    claimed_success: bool = True
    note: str = ""


@dataclass(slots=True)
class TaskDefinition:
    task_id: str
    title: str
    kind: str
    oracle_command: str
    replay: dict[str, list[ReplayAttemptDefinition]]
    prompt: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    definition_path: str = ""


@dataclass(slots=True)
class RunAttempt:
    attempt_index: int
    candidate: str
    claimed_success: bool
    oracle_passed: bool
    oracle_exit_code: int
    duration_s: float
    stdout: str
    stderr: str
    note: str = ""


@dataclass(slots=True)
class RunLedger:
    task_id: str
    mode: str
    started_at: str
    finished_at: str
    attempts: list[RunAttempt] = field(default_factory=list)


@dataclass(slots=True)
class ProofCard:
    task_id: str
    mode: str
    verdict: str
    verified: bool
    unsafe_claim: bool
    attempt_count: int
    retries_used: int
    summary: str
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkTaskResult:
    task_id: str
    mode: str
    verified: bool
    unsafe_claim: bool
    attempt_count: int
    retries_used: int
    duration_s: float
    ledger: RunLedger
    proof_card: ProofCard
    ledger_path: str = ""
    proof_card_path: str = ""


@dataclass(slots=True)
class BenchmarkComparison:
    run_id: str
    generated_at: str
    baseline_results: list[BenchmarkTaskResult]
    treatment_results: list[BenchmarkTaskResult]
    baseline_metrics: dict[str, float | int]
    treatment_metrics: dict[str, float | int]
    delta_metrics: dict[str, float]
    comparison_path: str = ""
    report_path: str = ""


def to_builtin(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_builtin(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    return value

