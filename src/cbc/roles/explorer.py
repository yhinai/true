from __future__ import annotations

from pathlib import Path
from typing import Any

from cbc.api.store import list_benchmarks, list_runs


def explore_artifacts(artifacts_root: Path | str = "artifacts", limit: int = 50) -> dict[str, Any]:
    """Phase 9 explorer helper that surfaces what evidence exists."""
    root = Path(artifacts_root)
    return {
        "artifacts_root": str(root.resolve()),
        "runs": list_runs(root, limit=limit),
        "benchmarks": list_benchmarks(root, limit=limit),
    }
