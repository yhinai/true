from __future__ import annotations

from pathlib import Path

from cbc.models import ProofCard, RetryTranscript, RunLedger, VerificationReport
from cbc.storage.artifacts import write_json, write_markdown


def persist_run_artifacts(
    artifact_dir: Path,
    *,
    ledger: RunLedger,
    transcript: RetryTranscript,
    verification: VerificationReport,
    proof_card: ProofCard,
) -> None:
    write_json(artifact_dir / "run_ledger.json", ledger.model_dump(mode="json"))
    write_json(artifact_dir / "retry_transcript.json", transcript.model_dump(mode="json"))
    write_json(artifact_dir / "verification_report.json", verification.model_dump(mode="json"))
    write_json(artifact_dir / "run_artifact.json", build_run_artifact(ledger, verification))
    write_markdown(artifact_dir / "proof_card.md", render_proof_card(proof_card))


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


def build_run_artifact(ledger: RunLedger, verification: VerificationReport) -> dict[str, object]:
    return {
        "run_id": ledger.run_id,
        "task_id": ledger.task_id,
        "title": ledger.title,
        "mode": ledger.mode,
        "changed_files": verification.changed_files,
        "unsafe_claim": ledger.unsafe_claims > 0,
        "verification": {
            "status": verification.verdict.value,
            "checks": [check.model_dump(mode="json") for check in verification.checks],
            "summary": verification.summary,
        },
        "artifacts": {
            "artifact_dir": str(ledger.artifact_dir),
            "workspace_dir": str(ledger.workspace_dir),
        },
    }
