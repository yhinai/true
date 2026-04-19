"""Factory that converts loop state into a final RunLedger."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from cbc.controller.run_state import RunState
from cbc.models import (
    AttemptRecord,
    CandidateResult,
    PlanArtifact,
    ProofCard,
    RunLedger,
    VerificationReport,
)


def build_final_ledger(
    *,
    state: RunState,
    attempts: list[AttemptRecord],
    final_verification: VerificationReport,
    proof_card: ProofCard,
    run_id: str,
    title: str,
    mode: Literal["baseline", "treatment", "review"],
    controller_mode: Literal["sequential", "gearbox"],
    selected_candidate_id: str | None,
    adapter: str,
    artifact_dir: Path,
    workspace_dir: Path,
    plan: PlanArtifact,
    candidate_results: list[CandidateResult],
    unsafe_claims: int,
    model_calls_used: int,
    final_summary: str,
) -> RunLedger:
    prompt_tokens = sum(attempt.usage.prompt_tokens for attempt in attempts)
    completion_tokens = sum(attempt.usage.completion_tokens for attempt in attempts)
    total_tokens = sum(attempt.usage.total_tokens for attempt in attempts)
    costs = [
        attempt.usage.estimated_cost_usd
        for attempt in attempts
        if attempt.usage.estimated_cost_usd is not None
    ]
    adapter_failure_reasons = [
        reason
        for reason in (attempt.adapter_failure_reason for attempt in attempts)
        if reason
    ]
    ended_at = state.completed_at if state.completed_at is not None else datetime.now(UTC)

    return RunLedger(
        run_id=run_id,
        task_id=state.task_id,
        title=title,
        mode=mode,
        controller_mode=controller_mode,
        selected_candidate_id=selected_candidate_id,
        verdict=final_verification.verdict,
        adapter=adapter,
        artifact_dir=artifact_dir,
        workspace_dir=workspace_dir,
        plan=plan,
        attempts=attempts,
        candidate_results=candidate_results,
        unsafe_claims=unsafe_claims,
        model_calls_used=model_calls_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=sum(costs) if costs else None,
        adapter_failure_reasons=adapter_failure_reasons,
        final_summary=final_summary,
        started_at=state.started_at,
        ended_at=ended_at,
    )
