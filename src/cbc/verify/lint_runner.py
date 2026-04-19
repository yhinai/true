from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus
from cbc.verify.env_utils import scrub_env


def run_lint(workspace: Path, command: str = "python3 -m compileall .") -> CheckResult:
    if shutil.which("python3") is None:
        return CheckResult(name="lint", command=command, status=CheckStatus.SKIPPED, stdout="python3 unavailable")
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
        name="lint",
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
