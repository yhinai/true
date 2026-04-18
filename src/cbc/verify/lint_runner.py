from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from cbc.models import CheckResult, CheckStatus


def run_lint(workspace: Path, command: str = "python3 -m compileall .") -> CheckResult:
    if shutil.which("python3") is None:
        return CheckResult(name="lint", command=command, status=CheckStatus.SKIPPED, stdout="python3 unavailable")
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
        name="lint",
        command=command,
        status=status,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )
