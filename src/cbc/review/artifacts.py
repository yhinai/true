from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def read_json(path: Path) -> dict[str, Any]:
    """Load a JSON artifact from disk."""
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Artifact at {path} must be a JSON object.")
    return loaded


def iter_json_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def pick_first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None
