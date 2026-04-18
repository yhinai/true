from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CrossHairResult:
    status: str
    command: tuple[str, ...]
    returncode: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    message: str | None = None
    issues: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "command": list(self.command),
            "returncode": self.returncode,
            "duration_seconds": self.duration_seconds,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "message": self.message,
            "issues": list(self.issues),
        }


def run_crosshair(
    target: str,
    *,
    timeout_seconds: float = 20.0,
    working_directory: str | Path | None = None,
    extra_args: list[str] | None = None,
) -> CrossHairResult:
    command_prefix = _resolve_crosshair_command()
    if command_prefix is None:
        return CrossHairResult(
            status="unavailable",
            command=(),
            returncode=None,
            duration_seconds=0.0,
            stdout="",
            stderr="",
            message="CrossHair is not installed.",
        )

    command = [
        *command_prefix,
        "check",
        target,
        "--analysis_kind=PEP316,icontract,asserts",
        f"--per_path_timeout={max(1, int(timeout_seconds))}",
    ]
    if extra_args:
        command.extend(extra_args)

    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(working_directory) if working_directory is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return CrossHairResult(
            status="timeout",
            command=tuple(command),
            returncode=None,
            duration_seconds=time.monotonic() - start,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
            message=f"CrossHair timed out after {timeout_seconds:.1f}s.",
        )

    duration = time.monotonic() - start
    issues = tuple(
        line.strip()
        for line in completed.stdout.splitlines()
        if ":" in line and line.strip()
    )
    status = "passed" if completed.returncode == 0 else "failed"

    return CrossHairResult(
        status=status,
        command=tuple(command),
        returncode=completed.returncode,
        duration_seconds=duration,
        stdout=completed.stdout,
        stderr=completed.stderr,
        message=None if status == "passed" else "CrossHair reported potential issues.",
        issues=issues,
    )


def _resolve_crosshair_command() -> list[str] | None:
    binary = shutil.which("crosshair")
    if binary:
        return [binary]
    if importlib.util.find_spec("crosshair") is not None:
        return [sys.executable, "-m", "crosshair"]
    return None
