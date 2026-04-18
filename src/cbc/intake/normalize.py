from __future__ import annotations

from pathlib import Path

import yaml

from cbc.models import TaskSpec


def load_task(path: Path) -> TaskSpec:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["workspace"] = (path.parent / payload["workspace"]).resolve()
    if payload.get("replay_file"):
        payload["replay_file"] = (path.parent / payload["replay_file"]).resolve()
    return TaskSpec.model_validate(payload)
