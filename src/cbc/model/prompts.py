from __future__ import annotations

import json
from pathlib import Path

from cbc.models import PlanArtifact, VerificationReport


JSON_RESPONSE_CONTRACT = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "claimed_success": {"type": "boolean"},
        "notes": {"type": "array", "items": {"type": "string"}},
        "writes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "executable": {"type": "boolean"},
                },
                "required": ["path", "content", "executable"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "claimed_success", "notes", "writes"],
    "required": ["summary", "claimed_success", "notes", "writes"],
    "additionalProperties": False,
}


def write_schema_file(path: Path) -> Path:
    path.write_text(json.dumps(JSON_RESPONSE_CONTRACT, indent=2), encoding="utf-8")
    return path


def build_coder_prompt(task_prompt: str, plan: PlanArtifact, evidence: str | None = None) -> str:
    lines = [
        "You are the Coder role inside a verification-first harness.",
        "Return JSON that matches the provided schema exactly.",
        "Only write files inside the allowed scope.",
        "",
        f"Task:\n{task_prompt}",
        "",
        f"Allowed files: {', '.join(plan.allowed_files) if plan.allowed_files else '(none specified)'}",
        f"Required checks: {', '.join(plan.required_checks) if plan.required_checks else '(task oracle only)'}",
    ]
    if plan.doubt_points:
        lines.append(f"Doubt points: {', '.join(plan.doubt_points)}")
    if evidence:
        lines.extend(["", "Retry evidence from the deterministic verifier:", evidence])
    return "\n".join(lines)


def summarize_verification_for_retry(report: VerificationReport) -> str:
    if report.verdict.value == "VERIFIED":
        return "Verifier passed."

    details: list[str] = []
    for check in report.checks:
        if check.status.value == "failed":
            excerpt = (check.stderr or check.stdout).strip()
            if excerpt:
                details.append(f"{check.name} failed:\n{excerpt[:1500]}")
            else:
                details.append(f"{check.name} failed with exit code {check.exit_code}.")
    if report.counterexample:
        details.append(f"Counterexample: {report.counterexample}")
    return "\n\n".join(details) if details else report.summary
