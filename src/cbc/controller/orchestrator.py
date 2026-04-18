from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.controller.artifact_flow import persist_run_artifacts
from cbc.controller.budgets import normalize_max_attempts
from cbc.controller.checkpoints import checkpoint_name
from cbc.controller.retries import should_retry
from cbc.model.codex_exec import CodexExecAdapter
from cbc.model.prompts import summarize_verification_for_retry, write_schema_file
from cbc.model.replay import ReplayModelAdapter
from cbc.models import AttemptRecord, ProofCard, RetryTranscript, RunLedger, TaskSpec, VerificationVerdict
from cbc.roles.coder import run_coder
from cbc.roles.planner import build_plan
from cbc.storage.artifacts import create_artifact_dir
from cbc.storage.runs import save_run
from cbc.verify.core import verify_workspace
from cbc.workspace.git_safety import describe_workspace_safety
from cbc.workspace.patching import apply_writes
from cbc.workspace.staging import stage_workspace


def resolve_codex_config(task: TaskSpec, config: AppConfig):
    task_codex = task.codex
    return config.codex.model_copy(
        update={
            "default_model": task_codex.model if task_codex.model is not None else config.codex.default_model,
            "sandbox": task_codex.sandbox if task_codex.sandbox is not None else config.codex.sandbox,
            "profile": task_codex.profile if task_codex.profile is not None else config.codex.profile,
            "config_overrides": [*config.codex.config_overrides, *task_codex.config_overrides],
            "add_dirs": [*config.codex.add_dirs, *task_codex.add_dirs],
            "skip_git_repo_check": (
                task_codex.skip_git_repo_check
                if task_codex.skip_git_repo_check is not None
                else config.codex.skip_git_repo_check
            ),
            "dangerously_bypass_approvals": (
                task_codex.dangerously_bypass_approvals
                if task_codex.dangerously_bypass_approvals is not None
                else config.codex.dangerously_bypass_approvals
            ),
        }
    )


def load_adapter(task: TaskSpec, config: AppConfig):
    if task.adapter == "codex":
        return CodexExecAdapter(resolve_codex_config(task, config))
    assert task.replay_file is not None
    return ReplayModelAdapter(task.replay_file)


def run_task(task: TaskSpec, *, mode: str, config: AppConfig = DEFAULT_CONFIG) -> RunLedger:
    run_id = uuid4().hex[:12]
    artifact_dir = create_artifact_dir(config.paths.artifacts_dir, "runs")
    schema_path = artifact_dir / "response_schema.json"
    write_schema_file(schema_path)

    started_at = datetime.now(UTC)
    workspace = stage_workspace(task.workspace)
    plan = build_plan(task)
    adapter = load_adapter(task, config)
    max_attempts = normalize_max_attempts(task.retry_budget, config.retry.max_attempts, mode)

    attempts: list[AttemptRecord] = []
    unsafe_claims = 0
    evidence: str | None = None

    for attempt in range(1, max_attempts + 1):
        response, events, prompt = run_coder(
            adapter,
            task_prompt=task.prompt,
            plan=plan,
            workspace=workspace,
            attempt=attempt,
            evidence=evidence,
            schema_path=schema_path,
        )
        changed_files = apply_writes(workspace, response.writes, plan.allowed_files)
        verification = verify_workspace(
            workspace,
            task=task,
            changed_files=changed_files,
            claimed_success=response.claimed_success,
        )
        unsafe_claims += int(verification.unsafe_claim_detected)
        attempt_record = AttemptRecord(
            attempt=attempt,
            prompt=prompt,
            evidence=evidence,
            model_response=response,
            verification=verification,
            started_at=started_at,
            ended_at=datetime.now(UTC),
        )
        attempts.append(attempt_record)
        if verification.verdict == VerificationVerdict.VERIFIED or not should_retry(attempt, max_attempts, verification):
            break
        evidence = summarize_verification_for_retry(verification)

    final_verification = attempts[-1].verification
    safety_note = describe_workspace_safety(task.workspace, workspace)
    checkpoints = [checkpoint_name(attempt.attempt, workspace) for attempt in attempts]
    final_summary = f"{final_verification.summary} {safety_note} Checkpoints: {', '.join(checkpoints)}."
    ended_at = datetime.now(UTC)

    ledger = RunLedger(
        run_id=run_id,
        task_id=task.task_id,
        title=task.title,
        mode=mode,
        verdict=final_verification.verdict,
        adapter=adapter.name,
        artifact_dir=artifact_dir,
        workspace_dir=workspace,
        plan=plan,
        attempts=attempts,
        unsafe_claims=unsafe_claims,
        final_summary=final_summary,
        started_at=started_at,
        ended_at=ended_at,
    )
    proof_card = ProofCard(
        run_id=run_id,
        task_id=task.task_id,
        mode=mode,
        verdict=ledger.verdict,
        unsafe_claims=unsafe_claims,
        attempts=len(attempts),
        summary=final_summary,
        proof_points=[
            f"deterministic_verdict={ledger.verdict.value}",
            f"unsafe_claims={unsafe_claims}",
            f"adapter={adapter.name}",
            f"workspace_isolation={workspace}",
        ],
        artifact_dir=artifact_dir,
    )
    persist_run_artifacts(
        artifact_dir,
        ledger=ledger,
        transcript=RetryTranscript(run_id=run_id, attempts=attempts),
        verification=final_verification,
        proof_card=proof_card,
    )
    save_run(config.paths.storage_db, ledger)
    return ledger
