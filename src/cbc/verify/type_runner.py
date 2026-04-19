from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus
from cbc.verify.env_utils import scrub_env


def run_typecheck(workspace: Path, enabled: bool = False, command: str | None = None) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="typecheck",
            command="disabled",
            status=CheckStatus.SKIPPED,
            stdout="Type checking is disabled for this task.",
            details={"policy_reason": "disabled_in_task_config"},
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
                details={"policy_reason": "tool_unavailable"},
            )

    started = time.perf_counter()
    env = scrub_env(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        shlex.split(resolved_command),
        cwd=workspace,
        shell=False,
        env=env,
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
