from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.models import OracleSpec, TaskSpec
from cbc.graph.mismatch import detect_bounded_signature_mismatches
from cbc.verify.core import verify_workspace
from cbc.verify.hypothesis_runner import run_property_cases


def test_bounded_signature_reasoning_catches_mismatch() -> None:
    source_text = """
def normalize(value: int) -> int:
    return value + 1

def middle(user_input: int) -> int:
    return normalize(user_input, 7)

def entry(seed: int) -> int:
    return middle(seed)
"""

    shallow = detect_bounded_signature_mismatches(
        source_text,
        roots=["entry"],
        max_depth=0,
    )
    assert shallow == ()

    deep = detect_bounded_signature_mismatches(
        source_text,
        roots=["entry"],
        max_depth=2,
    )
    assert any(
        mismatch.caller == "middle"
        and mismatch.callee == "normalize"
        and mismatch.kind == "too_many_positional"
        for mismatch in deep
    )


def test_property_runner_emits_counterexample_artifact(tmp_path: Path) -> None:
    def even_only(number: int) -> None:
        assert number % 2 == 0, "expected an even number"

    result = run_property_cases(
        even_only,
        [2, 4, 5, 8],
        checker_name="even_only",
        artifact_dir=tmp_path,
        artifact_name="counterexample.json",
    )

    assert result.status == "failed"
    assert result.counterexample is not None
    assert result.counterexample["input"] == 5
    assert result.artifact_path is not None

    artifact_path = Path(result.artifact_path)
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["checker"] == "even_only"
    assert payload["input"] == 5
    assert payload["error_type"] == "AssertionError"


def test_verification_options_run_real_commands(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    task = TaskSpec(
        task_id="verification_options",
        title="Exercise verification commands",
        prompt="noop",
        workspace=tmp_path,
        adapter="codex",
        allowed_files=["app.py"],
        oracles=[OracleSpec(name="oracle", kind="python", command="-c \"print('ok')\"")],
        verification={
            "typecheck_enabled": True,
            "typecheck_command": "python3 -m py_compile app.py",
            "coverage_enabled": True,
            "coverage_command": "python3 -c \"print('coverage-ok')\"",
        },
    )

    report = verify_workspace(
        tmp_path,
        task=task,
        changed_files=["app.py"],
        claimed_success=True,
    )

    assert report.verdict.value == "VERIFIED"
    by_name = {check.name: check for check in report.checks}
    assert by_name["typecheck"].status.value == "passed"
    assert by_name["coverage"].status.value == "passed"


def test_structural_check_catches_cross_file_signature_mismatch(tmp_path: Path) -> None:
    (tmp_path / "helpers.py").write_text(
        "def normalize(value: int) -> int:\n    return value + 1\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "from helpers import normalize\n\n"
        "def entry(seed: int) -> int:\n"
        "    return normalize(seed, 7)\n",
        encoding="utf-8",
    )

    task = TaskSpec(
        task_id="structural_mismatch",
        title="Catch bounded structural mismatch",
        prompt="noop",
        workspace=tmp_path,
        adapter="codex",
        allowed_files=["main.py", "helpers.py"],
        oracles=[OracleSpec(name="oracle", kind="python", command="-c \"print('ok')\"")],
        tags=["python"],
    )

    report = verify_workspace(
        tmp_path,
        task=task,
        changed_files=["main.py"],
        claimed_success=True,
    )

    assert report.verdict.value == "FALSIFIED"
    by_name = {check.name: check for check in report.checks}
    assert by_name["structural"].status.value == "failed"
    mismatches = by_name["structural"].details["mismatches"]
    assert mismatches[0]["callee_function"] == "normalize"
    assert mismatches[0]["kind"] == "too_many_positional"
