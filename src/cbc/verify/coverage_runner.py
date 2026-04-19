from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_coverage(workspace: Path, enabled: bool = False, command: str | None = None) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="coverage",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Coverage is disabled for this task.",
            details={"policy_reason": "disabled_in_task_config"},
        )
    if not command:
        return CheckResult(
            name="coverage",
            command="unconfigured",
            status=CheckStatus.SKIPPED,
            stdout="Coverage requested but no coverage command was configured for this task.",
            details={"policy_reason": "missing_command"},
        )

    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=workspace,
        shell=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    status = CheckStatus.PASSED if completed.returncode == 0 else CheckStatus.FAILED
    return CheckResult(
        name="coverage",
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
