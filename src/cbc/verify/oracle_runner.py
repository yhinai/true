from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus, OracleSpec
from cbc.verify.env_utils import scrub_env


def run_oracle(workspace: Path, oracle: OracleSpec) -> CheckResult:
    started = time.perf_counter()
    if oracle.kind == "pytest":
        command = f"python3 -m pytest {oracle.command}"
    elif oracle.kind == "python":
        command = f"python3 {oracle.command}"
    else:
        command = oracle.command

    env = scrub_env(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        shlex.split(command),
        cwd=workspace,
        shell=False,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    status = CheckStatus.PASSED if completed.returncode in oracle.success_exit_codes else CheckStatus.FAILED
    return CheckResult(
        name=oracle.name,
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
