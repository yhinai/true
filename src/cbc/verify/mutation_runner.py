from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_mutation(
    workspace: Path,
    *,
    enabled: bool = False,
    command: str | None = None,
    skip_reason: str = "disabled_in_task_config",
) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="mutation",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Mutation testing is intentionally cut by default.",
            details={"policy_reason": skip_reason},
        )
    if not command:
        return CheckResult(
            name="mutation",
            command="unconfigured",
            status=CheckStatus.SKIPPED,
            stdout="Mutation testing requested but no command was configured for this task.",
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
        name="mutation",
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
