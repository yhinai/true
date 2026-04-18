from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


def create_artifact_dir(root: Path, prefix: str) -> Path:
    artifact_dir = root / prefix / uuid4().hex[:12]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
