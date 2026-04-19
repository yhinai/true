from __future__ import annotations

from pathlib import Path

from cbc.headless_contract import RUN_ARTIFACT_KIND, contract_metadata
from cbc.models import CandidateResult, ExplorerArtifact, ProofCard, RetryTranscript, RunLedger, VerificationReport
from cbc.review.ci import build_ci_report, render_ci_report
from cbc.review.report import compose_review_report
from cbc.storage.artifacts import write_json, write_markdown


def persist_run_artifacts(
    artifact_dir: Path,
    *,
    ledger: RunLedger,
    transcript: RetryTranscript,
    verification: VerificationReport,
    proof_card: ProofCard,
    diff_summary: dict[str, object],
    explorer: ExplorerArtifact | None = None,
    scheduler_trace: dict[str, object] | None = None,
    risk_artifact: dict[str, object] | None = None,
) -> None:
    run_artifact = build_run_artifact(
        ledger,
        verification,
        diff_summary=diff_summary,
        explorer=explorer,
        scheduler_trace=scheduler_trace,
        risk_artifact=risk_artifact,
    )
    review_report = compose_review_report(run_artifact)
    ci_report = build_ci_report(review_report)

    write_json(artifact_dir / "run_ledger.json", ledger.model_dump(mode="json"))
    write_json(artifact_dir / "retry_transcript.json", transcript.model_dump(mode="json"))
    write_json(artifact_dir / "verification_report.json", verification.model_dump(mode="json"))
    write_json(artifact_dir / "diff_summary.json", diff_summary)
    write_json(artifact_dir / "run_artifact.json", run_artifact)
    write_json(artifact_dir / "review_report.json", review_report)
    write_json(artifact_dir / "merge_gate.json", review_report["summary"]["merge_gate"])
    write_json(artifact_dir / "ci_report.json", ci_report)
    if explorer is not None:
        write_json(artifact_dir / "explorer_artifact.json", explorer.model_dump(mode="json"))
    if scheduler_trace is not None:
        write_json(artifact_dir / "scheduler_trace.json", scheduler_trace)
    if risk_artifact is not None:
        write_json(artifact_dir / "risk_artifact.json", risk_artifact)
    persist_candidate_artifacts(artifact_dir, ledger.candidate_results)
    write_markdown(artifact_dir / "proof_card.md", render_proof_card(proof_card))
    write_markdown(artifact_dir / "ci_report.md", render_ci_report(ci_report))


def render_proof_card(card: ProofCard) -> str:
    bullets = "\n".join(f"- {point}" for point in card.proof_points)
    return (
        f"# Proof Card\n\n"
        f"- Run ID: `{card.run_id}`\n"
        f"- Task: `{card.task_id}`\n"
        f"- Mode: `{card.mode}`\n"
        f"- Verdict: `{card.verdict.value}`\n"
        f"- Attempts: `{card.attempts}`\n"
        f"- Unsafe claims: `{card.unsafe_claims}`\n\n"
        f"## Summary\n{card.summary}\n\n"
        f"## Proof Points\n{bullets}\n"
    )


def build_run_artifact(
    ledger: RunLedger,
    verification: VerificationReport,
    *,
    diff_summary: dict[str, object],
    explorer: ExplorerArtifact | None = None,
    scheduler_trace: dict[str, object] | None = None,
    risk_artifact: dict[str, object] | None = None,
) -> dict[str, object]:
    generated_tests = []
    controller_budget: dict[str, object] = {}
    budget_spent: dict[str, object] = {}
    if scheduler_trace is not None:
        controller_budget = dict(scheduler_trace.get("budget", {}))
        budget_spent = {
            "model_calls_used": scheduler_trace.get("model_calls_used", 0),
            "attempts_executed": len(ledger.attempts),
            "candidate_evaluations": len(ledger.candidate_results),
        }
    for attempt in ledger.attempts:
        for check in attempt.verification.checks:
            artifact_path = check.details.get("regression_test_artifact")
            if isinstance(artifact_path, str):
                generated_tests.append(artifact_path)
    return {
        "contract": contract_metadata(RUN_ARTIFACT_KIND),
        "run_id": ledger.run_id,
        "task_id": ledger.task_id,
        "title": ledger.title,
        "mode": ledger.mode,
        "controller": {
            "mode": ledger.controller_mode,
            "selected_candidate_id": ledger.selected_candidate_id,
            "candidate_count": len(ledger.candidate_results),
            "budget": controller_budget,
            "budget_spent": budget_spent,
            "scheduler_trace_path": str(ledger.artifact_dir / "scheduler_trace.json"),
        },
        "changed_files": verification.changed_files,
        "unsafe_claim": ledger.unsafe_claims > 0,
        "diff": diff_summary,
        "generated_test_artifacts": generated_tests,
        "verification": {
            "status": verification.verdict.value,
            "checks": [check.model_dump(mode="json") for check in verification.checks],
            "summary": verification.summary,
            "counterexample": verification.counterexample,
            "policy": verification.check_policy,
        },
        "artifacts": {
            "artifact_dir": str(ledger.artifact_dir),
            "workspace_dir": str(ledger.workspace_dir),
        },
        "supporting_checks": list(ledger.plan.required_checks),
        "explorer": explorer.model_dump(mode="json") if explorer is not None else None,
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "candidate_role": candidate.candidate_role,
                "attempt": candidate.attempt,
                "selected": candidate.selected,
                "workspace_dir": str(candidate.workspace_dir),
                "score": candidate.score.model_dump(mode="json"),
                "verification": {
                    "status": candidate.verification.verdict.value,
                    "unsafe_claim": candidate.verification.unsafe_claim_detected,
                },
            }
            for candidate in ledger.candidate_results
        ],
        "scheduler_trace": scheduler_trace,
        "risk_artifact": risk_artifact,
    }


def persist_candidate_artifacts(artifact_dir: Path, candidates: list[CandidateResult]) -> None:
    for candidate in candidates:
        candidate_dir = artifact_dir / "candidate_artifacts" / candidate.candidate_id
        write_json(candidate_dir / "model_response.json", candidate.model_response.model_dump(mode="json"))
        write_json(candidate_dir / "verification_report.json", candidate.verification.model_dump(mode="json"))
        write_json(candidate_dir / "diff_summary.json", candidate.diff_summary)
        write_json(candidate_dir / "risk_artifact.json", candidate.risk_artifact)
        write_json(candidate_dir / "score.json", candidate.score.model_dump(mode="json"))
        write_markdown(candidate_dir / "prompt.txt", candidate.prompt)
