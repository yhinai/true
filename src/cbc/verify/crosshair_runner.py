from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus
from cbc.verify.env_utils import scrub_env


def run_crosshair(
    workspace: Path,
    *,
    enabled: bool = False,
    command: str | None = None,
    skip_reason: str = "disabled_in_task_config",
) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="crosshair",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="CrossHair is optional and non-blocking in this build.",
            details={"policy_reason": skip_reason},
        )
    if not command:
        return CheckResult(
            name="crosshair",
            command="unconfigured",
            status=CheckStatus.SKIPPED,
            stdout="CrossHair requested but no command was configured for this task.",
            details={"policy_reason": "missing_command"},
        )

    started = time.perf_counter()
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
    status = CheckStatus.PASSED if completed.returncode == 0 else CheckStatus.FAILED
    return CheckResult(
        name="crosshair",
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
