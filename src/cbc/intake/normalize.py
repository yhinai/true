from __future__ import annotations

from pathlib import Path

import yaml

from cbc.models import TaskSpec


def load_task(path: Path) -> TaskSpec:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["workspace"] = (path.parent / payload["workspace"]).resolve()
    if payload.get("replay_file"):
        payload["replay_file"] = (path.parent / payload["replay_file"]).resolve()
    codex_payload = payload.get("codex")
    if isinstance(codex_payload, dict) and codex_payload.get("add_dirs"):
        codex_payload["add_dirs"] = [
            ((path.parent / add_dir).resolve() if not Path(add_dir).is_absolute() else Path(add_dir).resolve())
            for add_dir in codex_payload["add_dirs"]
        ]
    return TaskSpec.model_validate(payload)
