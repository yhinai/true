from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .types import ReplayAttemptDefinition, TaskDefinition


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"Expected object in JSON file: {path}"
        raise ValueError(msg)
    return data


def load_task_definition(task_definition_path: Path) -> TaskDefinition:
    payload = _read_json(task_definition_path)
    replay_payload = payload.get("replay", {})
    replay: dict[str, list[ReplayAttemptDefinition]] = {}
    for mode, attempts in replay_payload.items():
        replay_attempts: list[ReplayAttemptDefinition] = []
        for attempt in attempts:
            candidate_path = (task_definition_path.parent / attempt["candidate"]).resolve()
            replay_attempts.append(
                ReplayAttemptDefinition(
                    candidate=str(candidate_path),
                    claimed_success=bool(attempt.get("claimed_success", True)),
                    note=str(attempt.get("note", "")),
                )
            )
        replay[mode] = replay_attempts

    return TaskDefinition(
        task_id=str(payload["task_id"]),
        title=str(payload.get("title", payload["task_id"])),
        kind=str(payload.get("kind", "oracle")),
        oracle_command=str(payload["oracle_command"]),
        replay=replay,
        prompt=str(payload.get("prompt", "")),
        metadata=dict(payload.get("metadata", {})),
        definition_path=str(task_definition_path.resolve()),
    )


def load_tasks_from_manifest(
    manifest_path: Path, include_task_ids: Iterable[str] | None = None
) -> list[TaskDefinition]:
    payload = _read_json(manifest_path)
    task_refs = payload.get("tasks", [])
    if not isinstance(task_refs, list):
        msg = f"manifest tasks must be a list: {manifest_path}"
        raise ValueError(msg)

    allowed = set(include_task_ids or [])
    use_filter = include_task_ids is not None
    tasks: list[TaskDefinition] = []
    for task_ref in task_refs:
        task_file = (manifest_path.parent / task_ref).resolve()
        task = load_task_definition(task_file)
        if use_filter and task.task_id not in allowed:
            continue
        tasks.append(task)

    if use_filter:
        found = {task.task_id for task in tasks}
        missing = allowed - found
        if missing:
            msg = f"Unknown task_ids requested from manifest: {sorted(missing)}"
            raise ValueError(msg)

    return tasks

