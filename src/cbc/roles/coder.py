from __future__ import annotations

from pathlib import Path

from cbc.model.adapter import ModelAdapter
from cbc.model.prompts import build_coder_prompt
from cbc.models import AdapterRunResult, ExplorerArtifact, PlanArtifact


def run_coder(
    adapter: ModelAdapter,
    *,
    task_prompt: str,
    plan: PlanArtifact,
    explorer: ExplorerArtifact | None,
    workspace: Path,
    attempt: int,
    candidate_index: int = 0,
    candidate_role: str = "primary",
    evidence: str | None,
    schema_path: Path | None,
) -> tuple[AdapterRunResult, str]:
    prompt = build_coder_prompt(task_prompt, plan, evidence, explorer, candidate_role)
    result = adapter.run(
        prompt=prompt,
        workspace=workspace,
        attempt=attempt,
        candidate_index=candidate_index,
        candidate_role=candidate_role,
        schema_path=schema_path,
    )
    return result, prompt
