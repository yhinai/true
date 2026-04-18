from __future__ import annotations

from pathlib import Path

from cbc.models import CheckResult, OracleSpec
from cbc.verify.oracle_runner import run_oracle


def run_pytest_check(workspace: Path, target: str) -> CheckResult:
    return run_oracle(workspace, OracleSpec(name="pytest", kind="pytest", command=target))
