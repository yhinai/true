from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from .schema import VerificationOutcome, VerificationStatus


class CrossHairVerifier:
    def __init__(self, python_bin: str = ".venv/bin/python", timeout_seconds: float = 5.0) -> None:
        candidate = Path(python_bin)
        if candidate.is_absolute():
            self.python_bin = str(candidate)
        else:
            self.python_bin = str((Path.cwd() / candidate).absolute())
        self.timeout_seconds = timeout_seconds

    def verify_source(self, source: str, function_name: str) -> VerificationOutcome:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "subject.py"
            target.write_text(source, encoding="utf-8")
            target_spec = str(target)
            line_number = self._find_function_line_number(source, function_name)
            if line_number is not None:
                target_spec = f"{target}:{line_number}"
            command = [
                self.python_bin,
                "-m",
                "crosshair",
                "check",
                "--analysis_kind=icontract",
                "--max_uninteresting_iterations",
                "3",
                "--per_path_timeout",
                str(self.timeout_seconds),
                target_spec,
            ]
            try:
                proc = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds + 5.0,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return VerificationOutcome(
                    status=VerificationStatus.UNPROVEN,
                    raw_output=(exc.stdout or "") + (exc.stderr or ""),
                    command=command,
                    timeout_seconds=self.timeout_seconds,
                )

        raw_output = "\n".join(part for part in [proc.stdout, proc.stderr] if part).strip()
        if proc.returncode == 0:
            explored_paths = self._extract_explored_paths(raw_output)
            return VerificationOutcome(
                status=VerificationStatus.VERIFIED,
                raw_output=raw_output or "No counterexamples found.",
                command=command,
                explored_paths=explored_paths,
            )
        if proc.returncode == 1:
            counterexample = self._extract_counterexample(raw_output)
            violated = self._extract_violated_condition(raw_output)
            return VerificationOutcome(
                status=VerificationStatus.FALSIFIED,
                raw_output=raw_output,
                command=command,
                counterexample=counterexample,
                violated_condition=violated,
            )
        return VerificationOutcome(
            status=VerificationStatus.UNPROVEN,
            raw_output=raw_output,
            command=command,
        )

    @staticmethod
    def _extract_counterexample(output: str) -> str | None:
        match = re.search(r"when calling (.+?) \(which", output)
        if match:
            return match.group(1)
        match = re.search(r"when calling ([^(]+\([^)\n]+\))", output)
        if match:
            return match.group(1)
        match = re.search(r"for any input:\s*(.+)", output)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_violated_condition(output: str) -> str | None:
        for line in output.splitlines():
            if "error:" in line:
                return line.split("error:", 1)[1].strip()
        return None

    @staticmethod
    def _extract_explored_paths(output: str) -> int | None:
        match = re.search(r"explored (\d+) paths", output)
        return int(match.group(1)) if match else None

    @staticmethod
    def _find_function_line_number(source: str, function_name: str) -> int | None:
        pattern = re.compile(rf"^\s*(?:async\s+def|def)\s+{re.escape(function_name)}\s*\(")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if pattern.search(line):
                return line_number
        return None
