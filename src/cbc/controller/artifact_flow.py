from __future__ import annotations

from pathlib import Path

from cbc.models import ExplorerArtifact, ProofCard, RetryTranscript, RunLedger, VerificationReport
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
) -> None:
    run_artifact = build_run_artifact(ledger, verification, diff_summary=diff_summary, explorer=explorer)
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
) -> dict[str, object]:
    generated_tests = []
    for attempt in ledger.attempts:
        for check in attempt.verification.checks:
            artifact_path = check.details.get("regression_test_artifact")
            if isinstance(artifact_path, str):
                generated_tests.append(artifact_path)
    return {
        "run_id": ledger.run_id,
        "task_id": ledger.task_id,
        "title": ledger.title,
        "mode": ledger.mode,
        "changed_files": verification.changed_files,
        "unsafe_claim": ledger.unsafe_claims > 0,
        "diff": diff_summary,
        "generated_test_artifacts": generated_tests,
        "verification": {
            "status": verification.verdict.value,
            "checks": [check.model_dump(mode="json") for check in verification.checks],
            "summary": verification.summary,
            "counterexample": verification.counterexample,
        },
        "artifacts": {
            "artifact_dir": str(ledger.artifact_dir),
            "workspace_dir": str(ledger.workspace_dir),
        },
        "explorer": explorer.model_dump(mode="json") if explorer is not None else None,
    }
