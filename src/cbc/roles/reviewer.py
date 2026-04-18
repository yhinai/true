from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from cbc.review.artifacts import read_json
from cbc.review.report import compose_review_report


def review_artifact(run_artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Role facade for Phase 6 review mode."""
    return compose_review_report(run_artifact)


def review_artifact_path(path: Path | str) -> dict[str, Any]:
    artifact_path = Path(path)
    run_artifact = read_json(artifact_path)
    report = review_artifact(run_artifact)
    report["artifact_path"] = str(artifact_path.resolve())
    return report
