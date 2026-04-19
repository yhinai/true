from __future__ import annotations

from typing import Final


HEADLESS_CONTRACT_VERSION: Final[str] = "2026-04-18.v1"

RUN_ARTIFACT_KIND: Final[str] = "cbc.run_artifact"
REVIEW_REPORT_KIND: Final[str] = "cbc.review_report"
CI_REPORT_KIND: Final[str] = "cbc.ci_report"
BENCHMARK_COMPARISON_KIND: Final[str] = "cbc.benchmark_comparison"
CONTROLLER_COMPARISON_KIND: Final[str] = "cbc.controller_comparison"


def contract_metadata(kind: str) -> dict[str, str]:
    return {"kind": kind, "version": HEADLESS_CONTRACT_VERSION}
