from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_typecheck(workspace: Path, enabled: bool = False, command: str | None = None) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="typecheck",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Type checking is disabled for this task.",
        )

    resolved_command = command
    if resolved_command is None:
        if shutil.which("mypy"):
            resolved_command = "mypy ."
        elif shutil.which("pyright"):
            resolved_command = "pyright"
        else:
            return CheckResult(
                name="typecheck",
                command="unavailable",
                status=CheckStatus.SKIPPED,
                stdout="Type checking requested but no supported typechecker is installed.",
            )

    started = time.perf_counter()
    completed = subprocess.run(
        resolved_command,
        cwd=workspace,
        shell=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    status = CheckStatus.PASSED if completed.returncode == 0 else CheckStatus.FAILED
    return CheckResult(
        name="typecheck",
        command=resolved_command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
