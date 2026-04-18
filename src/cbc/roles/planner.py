from __future__ import annotations

from cbc.models import PlanArtifact, TaskSpec


def build_plan(task: TaskSpec) -> PlanArtifact:
    return PlanArtifact(
        summary=f"Plan for {task.task_id}: edit only the allowed files and satisfy the deterministic oracle.",
        allowed_files=task.allowed_files,
        required_checks=task.required_checks or [oracle.name for oracle in task.oracles],
        doubt_points=task.doubt_points,
    )
