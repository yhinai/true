from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.controller.artifact_flow import persist_run_artifacts
from cbc.controller.budgets import normalize_max_attempts
from cbc.controller.checkpoints import checkpoint_name
from cbc.controller.retries import should_retry
from cbc.model.codex_exec import CodexExecAdapter
from cbc.model.prompts import summarize_verification_for_retry, write_schema_file
from cbc.model.replay import ReplayModelAdapter
from cbc.models import (
    AttemptRecord,
    CandidateResult,
    CandidateScore,
    ExplorerArtifact,
    ModelResponse,
    ProofCard,
    RetryTranscript,
    RunLedger,
    TaskSpec,
    VerificationReport,
    VerificationVerdict,
)
from cbc.roles.coder import run_coder
from cbc.roles.explorer import build_explorer_artifact
from cbc.roles.planner import build_plan
from cbc.roles.risk_worker import build_risk_artifact
from cbc.storage.artifacts import create_artifact_dir
from cbc.storage.runs import save_run
from cbc.verify.core import verify_workspace
from cbc.workspace.diffing import summarize_workspace_diff
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


def run_task(
    task: TaskSpec,
    *,
    mode: str,
    config: AppConfig = DEFAULT_CONFIG,
    controller_mode: str | None = None,
) -> RunLedger:
    run_id = uuid4().hex[:12]
    artifact_dir = create_artifact_dir(config.paths.artifacts_dir, "runs")
    schema_path = artifact_dir / "response_schema.json"
    write_schema_file(schema_path)

    started_at = datetime.now(UTC)
    workspace = stage_workspace(task.workspace)
    plan = build_plan(task)
    explorer = build_explorer_artifact(task, workspace)
    adapter = load_adapter(task, config)
    max_attempts = normalize_max_attempts(task.retry_budget, config.retry.max_attempts, mode)
    active_controller_mode = _resolve_controller_mode(mode, config, controller_mode)
    budget = config.controller.budget

    attempts: list[AttemptRecord] = []
    candidate_results: list[CandidateResult] = []
    scheduler_attempts: list[dict[str, Any]] = []
    unsafe_claims = 0
    evidence: str | None = None
    selected_candidate_id: str | None = None
    model_calls_used = 0

    for attempt in range(1, max_attempts + 1):
        should_branch = _should_use_gearbox(
            attempt=attempt,
            mode=mode,
            controller_mode=active_controller_mode,
            allow_retry_branch=budget.allow_alternate_candidates_on_retry,
            model_calls_used=model_calls_used,
            max_model_calls_per_run=budget.max_model_calls_per_run,
        )
        if should_branch:
            remaining_calls = max(budget.max_model_calls_per_run - model_calls_used, 0)
            candidate_count = min(max(budget.max_candidates_first_attempt, 1), remaining_calls)
            candidate_bundle = _run_gearbox_attempt(
                task=task,
                adapter=adapter,
                plan=plan,
                explorer=explorer,
                base_workspace=workspace,
                artifact_dir=artifact_dir,
                attempt=attempt,
                evidence=evidence,
                schema_path=schema_path,
                candidate_count=candidate_count,
            )
            if not candidate_bundle["candidates"]:
                raise RuntimeError("gearbox controller did not produce any candidate runs")
            model_calls_used += len(candidate_bundle["candidates"])
            candidate_results.extend(candidate_bundle["candidates"])
            scheduler_attempts.append(candidate_bundle["scheduler"])
            selected = candidate_bundle["selected"]
            workspace = selected.workspace_dir
            selected_candidate_id = selected.candidate_id
            verification = selected.verification
            unsafe_claims += int(verification.unsafe_claim_detected)
            attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    candidate_id=selected.candidate_id,
                    candidate_role=selected.candidate_role,
                    prompt=selected.prompt,
                    evidence=evidence,
                    model_response=selected.model_response,
                    verification=verification,
                    started_at=started_at,
                    ended_at=datetime.now(UTC),
                )
            )
        else:
            response, _events, prompt = run_coder(
                adapter,
                task_prompt=task.prompt,
                plan=plan,
                explorer=explorer,
                workspace=workspace,
                attempt=attempt,
                candidate_index=0,
                candidate_role="primary",
                evidence=evidence,
                schema_path=schema_path,
            )
            model_calls_used += 1
            changed_files = apply_writes(workspace, response.writes, plan.allowed_files)
            verification = verify_workspace(
                workspace,
                task=task,
                changed_files=changed_files,
                claimed_success=response.claimed_success,
                artifact_dir=artifact_dir,
            )
            unsafe_claims += int(verification.unsafe_claim_detected)
            attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    prompt=prompt,
                    evidence=evidence,
                    model_response=response,
                    verification=verification,
                    started_at=started_at,
                    ended_at=datetime.now(UTC),
                )
            )
            scheduler_attempts.append(
                {
                    "attempt": attempt,
                    "controller_mode": "sequential",
                    "selected_candidate_id": None,
                    "candidate_ids": [],
                    "model_calls_used": model_calls_used,
                }
            )
        if verification.verdict == VerificationVerdict.VERIFIED or not should_retry(attempt, max_attempts, verification):
            break
        evidence = summarize_verification_for_retry(verification)

    final_verification = attempts[-1].verification
    all_changed_files = _collect_changed_files(attempts)
    diff_summary = summarize_workspace_diff(task.workspace, workspace, changed_files=all_changed_files)
    safety_note = describe_workspace_safety(task.workspace, workspace)
    checkpoints = [checkpoint_name(attempt_record.attempt, workspace) for attempt_record in attempts]
    final_summary = f"{final_verification.summary} {safety_note} Checkpoints: {', '.join(checkpoints)}."
    ended_at = datetime.now(UTC)
    final_risk_artifact = build_risk_artifact(
        diff_summary=diff_summary,
        verification=final_verification,
        unsafe_claims=unsafe_claims,
    )
    scheduler_trace = {
        "controller_mode": active_controller_mode,
        "budget": {
            "max_model_calls_per_run": budget.max_model_calls_per_run,
            "max_candidates_first_attempt": budget.max_candidates_first_attempt,
            "allow_alternate_candidates_on_retry": budget.allow_alternate_candidates_on_retry,
        },
        "model_calls_used": model_calls_used,
        "selected_candidate_id": selected_candidate_id,
        "attempts": scheduler_attempts,
    }

    ledger = RunLedger(
        run_id=run_id,
        task_id=task.task_id,
        title=task.title,
        mode=mode,
        controller_mode=active_controller_mode,
        selected_candidate_id=selected_candidate_id,
        verdict=final_verification.verdict,
        adapter=adapter.name,
        artifact_dir=artifact_dir,
        workspace_dir=workspace,
        plan=plan,
        attempts=attempts,
        candidate_results=candidate_results,
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
            f"controller_mode={active_controller_mode}",
            f"workspace_isolation={workspace}",
            *_explorer_proof_points(explorer),
            *_candidate_proof_points(candidate_results, selected_candidate_id),
            *_property_proof_points(attempts),
        ],
        artifact_dir=artifact_dir,
    )
    persist_run_artifacts(
        artifact_dir,
        ledger=ledger,
        transcript=RetryTranscript(run_id=run_id, attempts=attempts),
        verification=final_verification,
        proof_card=proof_card,
        diff_summary=diff_summary,
        explorer=explorer,
        scheduler_trace=scheduler_trace,
        risk_artifact=final_risk_artifact,
    )
    save_run(config.paths.storage_db, ledger)
    return ledger


def review_workspace(task: TaskSpec, workspace_path: Path, *, config: AppConfig = DEFAULT_CONFIG) -> RunLedger:
    run_id = uuid4().hex[:12]
    artifact_dir = create_artifact_dir(config.paths.artifacts_dir, "runs")
    started_at = datetime.now(UTC)
    workspace = stage_workspace(workspace_path)
    plan = build_plan(task)
    changed_files = _discover_changed_files(task.workspace, workspace)
    requested_checks = _infer_review_checks(task, changed_files)
    verification = verify_workspace(
        workspace,
        task=task,
        changed_files=changed_files,
        claimed_success=False,
        requested_checks=requested_checks,
        artifact_dir=artifact_dir,
    )
    attempt = AttemptRecord(
        attempt=1,
        prompt="review existing workspace diff",
        model_response=ModelResponse(
            summary="review-only validation",
            claimed_success=False,
            writes=[],
            notes=[f"review_checks={', '.join(requested_checks)}"],
        ),
        verification=verification,
        started_at=started_at,
        ended_at=datetime.now(UTC),
    )
    safety_note = describe_workspace_safety(task.workspace, workspace)
    final_summary = f"{verification.summary} {safety_note} Checkpoints: {checkpoint_name(1, workspace)}."
    diff_summary = summarize_workspace_diff(task.workspace, workspace, changed_files=changed_files)
    risk_artifact = build_risk_artifact(
        diff_summary=diff_summary,
        verification=verification,
        unsafe_claims=0,
    )
    scheduler_trace = {
        "controller_mode": "sequential",
        "budget": {
            "max_model_calls_per_run": 0,
            "max_candidates_first_attempt": 0,
            "allow_alternate_candidates_on_retry": False,
        },
        "model_calls_used": 0,
        "selected_candidate_id": None,
        "attempts": [],
    }
    ledger = RunLedger(
        run_id=run_id,
        task_id=task.task_id,
        title=task.title,
        mode="review",
        controller_mode="sequential",
        selected_candidate_id=None,
        verdict=verification.verdict,
        adapter="review-workspace",
        artifact_dir=artifact_dir,
        workspace_dir=workspace,
        plan=plan,
        attempts=[attempt],
        candidate_results=[],
        unsafe_claims=0,
        final_summary=final_summary,
        started_at=started_at,
        ended_at=datetime.now(UTC),
    )
    proof_card = ProofCard(
        run_id=run_id,
        task_id=task.task_id,
        mode="review",
        verdict=ledger.verdict,
        unsafe_claims=0,
        attempts=1,
        summary=final_summary,
        proof_points=[
            f"deterministic_verdict={ledger.verdict.value}",
            f"review_checks={', '.join(requested_checks)}",
            f"workspace_isolation={workspace}",
            *_property_proof_points([attempt]),
        ],
        artifact_dir=artifact_dir,
    )
    persist_run_artifacts(
        artifact_dir,
        ledger=ledger,
        transcript=RetryTranscript(run_id=run_id, attempts=[attempt]),
        verification=verification,
        proof_card=proof_card,
        diff_summary=diff_summary,
        scheduler_trace=scheduler_trace,
        risk_artifact=risk_artifact,
    )
    save_run(config.paths.storage_db, ledger)
    return ledger


def _run_gearbox_attempt(
    *,
    task: TaskSpec,
    adapter,
    plan,
    explorer: ExplorerArtifact,
    base_workspace: Path,
    artifact_dir: Path,
    attempt: int,
    evidence: str | None,
    schema_path: Path,
    candidate_count: int,
) -> dict[str, Any]:
    candidates: list[CandidateResult] = []
    for candidate_index in range(candidate_count):
        candidate_id = f"candidate_{chr(ord('a') + candidate_index)}"
        candidate_role = "primary" if candidate_index == 0 else "alternate"
        candidate_workspace = stage_workspace(base_workspace)
        response, _events, prompt = run_coder(
            adapter,
            task_prompt=task.prompt,
            plan=plan,
            explorer=explorer,
            workspace=candidate_workspace,
            attempt=attempt,
            candidate_index=candidate_index,
            candidate_role=candidate_role,
            evidence=evidence,
            schema_path=schema_path,
        )
        changed_files = apply_writes(candidate_workspace, response.writes, plan.allowed_files)
        verification = verify_workspace(
            candidate_workspace,
            task=task,
            changed_files=changed_files,
            claimed_success=response.claimed_success,
            artifact_dir=artifact_dir / "candidate_artifacts" / candidate_id,
        )
        diff_summary = summarize_workspace_diff(base_workspace, candidate_workspace, changed_files=changed_files)
        risk_artifact = build_risk_artifact(
            diff_summary=diff_summary,
            verification=verification,
            unsafe_claims=int(verification.unsafe_claim_detected),
        )
        candidates.append(
            CandidateResult(
                candidate_id=candidate_id,
                candidate_role=candidate_role,
                attempt=attempt,
                prompt=prompt,
                model_response=response,
                verification=verification,
                workspace_dir=candidate_workspace,
                diff_summary=diff_summary,
                risk_artifact=risk_artifact,
                score=_score_candidate(verification, diff_summary),
            )
        )
    selected = _select_candidate(candidates)
    selected.selected = True
    return {
        "selected": selected,
        "candidates": candidates,
        "scheduler": {
            "attempt": attempt,
            "controller_mode": "gearbox",
            "selected_candidate_id": selected.candidate_id,
            "candidate_ids": [candidate.candidate_id for candidate in candidates],
            "scores": {
                candidate.candidate_id: candidate.score.model_dump(mode="json")
                for candidate in candidates
            },
            "model_calls_used": len(candidates),
        },
    }


def _resolve_controller_mode(mode: str, config: AppConfig, override: str | None) -> str:
    if mode != "treatment":
        return "sequential"
    selected = override or config.controller.mode
    return "gearbox" if selected == "gearbox" else "sequential"


def _should_use_gearbox(
    *,
    attempt: int,
    mode: str,
    controller_mode: str,
    allow_retry_branch: bool,
    model_calls_used: int,
    max_model_calls_per_run: int,
) -> bool:
    if mode != "treatment" or controller_mode != "gearbox":
        return False
    if model_calls_used >= max_model_calls_per_run:
        return False
    return attempt == 1 or allow_retry_branch


def _score_candidate(verification: VerificationReport, diff_summary: dict[str, Any]) -> CandidateScore:
    passed_checks = sum(1 for check in verification.checks if check.status.value == "passed")
    additions = 0
    deletions = 0
    for item in diff_summary.get("files", []):
        if isinstance(item, dict):
            additions += int(item.get("additions", 0))
            deletions += int(item.get("deletions", 0))
    return CandidateScore(
        passed_checks=passed_checks,
        unsafe_claim=verification.unsafe_claim_detected,
        changed_files=len(verification.changed_files),
        diff_additions=additions,
        diff_deletions=deletions,
    )


def _select_candidate(candidates: list[CandidateResult]) -> CandidateResult:
    return sorted(
        candidates,
        key=lambda candidate: (
            0 if candidate.verification.verdict == VerificationVerdict.VERIFIED else 1,
            -candidate.score.passed_checks,
            1 if candidate.score.unsafe_claim else 0,
            candidate.score.changed_files,
            candidate.score.diff_additions + candidate.score.diff_deletions,
            candidate.candidate_id,
        ),
    )[0]


def _collect_changed_files(attempts: list[AttemptRecord]) -> list[str]:
    changed: list[str] = []
    for attempt in attempts:
        changed.extend(attempt.verification.changed_files)
    return sorted(set(changed))


def _discover_changed_files(source: Path, staged: Path) -> list[str]:
    diff_summary = summarize_workspace_diff(source, staged)
    return [entry["path"] for entry in diff_summary["files"] if isinstance(entry, dict) and isinstance(entry.get("path"), str)]


def _infer_review_checks(task: TaskSpec, changed_files: list[str]) -> list[str]:
    if task.review_checks:
        return sorted(set(task.review_checks))

    selected = {"oracle", "lint"}
    if any(path.endswith(".py") for path in changed_files):
        selected.add("structural")
        if task.verification.typecheck_enabled:
            selected.add("typecheck")
        if task.verification.coverage_enabled:
            selected.add("coverage")
        if task.hypothesis is not None:
            selected.add("hypothesis")
    return sorted(selected)


def _property_proof_points(attempts: list[AttemptRecord]) -> list[str]:
    proof_points: list[str] = []
    for attempt in attempts:
        for check in attempt.verification.checks:
            regression_artifact = check.details.get("regression_test_artifact")
            if isinstance(regression_artifact, str):
                proof_points.append(f"generated_regression_test={regression_artifact}")
            counterexample_artifact = check.details.get("counterexample_artifact")
            if isinstance(counterexample_artifact, str):
                proof_points.append(f"counterexample_artifact={counterexample_artifact}")
    return proof_points


def _explorer_proof_points(explorer: ExplorerArtifact) -> list[str]:
    proof_points: list[str] = []
    if explorer.likely_targets:
        proof_points.append(f"explorer_targets={','.join(explorer.likely_targets)}")
    if explorer.nearby_tests:
        proof_points.append(f"explorer_tests={','.join(explorer.nearby_tests)}")
    return proof_points


def _candidate_proof_points(candidates: list[CandidateResult], selected_candidate_id: str | None) -> list[str]:
    proof_points: list[str] = []
    if selected_candidate_id:
        proof_points.append(f"selected_candidate={selected_candidate_id}")
    if candidates:
        proof_points.append(f"candidate_count={len(candidates)}")
    return proof_points
