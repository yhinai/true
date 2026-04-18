from __future__ import annotations

from pathlib import Path

from cbc.model.adapter import ModelAdapter
from cbc.model.prompts import build_coder_prompt
from cbc.models import ExplorerArtifact, ModelEvent, ModelResponse, PlanArtifact


def run_coder(
    adapter: ModelAdapter,
    *,
    task_prompt: str,
    plan: PlanArtifact,
    explorer: ExplorerArtifact | None,
    workspace: Path,
    attempt: int,
    evidence: str | None,
    schema_path: Path | None,
) -> tuple[ModelResponse, list[ModelEvent], str]:
    prompt = build_coder_prompt(task_prompt, plan, evidence, explorer)
    response, events = adapter.run(prompt=prompt, workspace=workspace, attempt=attempt, schema_path=schema_path)
    return response, events, prompt
