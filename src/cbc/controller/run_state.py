"""Run-level state container for the orchestrator loop."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cbc.models import VerificationVerdict


class IterationRecord(BaseModel):
    iteration: int
    verdict: VerificationVerdict
    files_modified: list[Path] = Field(default_factory=list)
    error_summary: str = ""


class AttemptResult(BaseModel):
    verdict: VerificationVerdict
    candidate_index: int | None = None
    error_summary: str = ""
    files_modified: list[Path] = Field(default_factory=list)


class RunState(BaseModel):
    task_id: str
    iteration: int = 0
    max_iterations: int
    failure_context: list[str] = Field(default_factory=list)
    files_modified: set[Path] = Field(default_factory=set)
    iteration_history: list[IterationRecord] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None

    def append_failure(self, summary: str) -> None:
        self.failure_context.append(summary)
        if len(self.failure_context) > 10:
            self.failure_context = self.failure_context[-10:]

    def record_iteration(self, record: IterationRecord) -> None:
        self.iteration_history.append(record)
        for path in record.files_modified:
            self.files_modified.add(path)
