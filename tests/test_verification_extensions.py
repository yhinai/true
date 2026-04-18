from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.models import HypothesisCheckSpec, OracleSpec, TaskSpec
from cbc.graph.mismatch import detect_bounded_signature_mismatches
from cbc.verify.core import verify_workspace
from cbc.verify.hypothesis_runner import render_regression_test, run_property_cases


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


def test_render_regression_test_writes_replayable_pytest_file(tmp_path: Path) -> None:
    path = render_regression_test(
        artifact_dir=tmp_path,
        spec=HypothesisCheckSpec(
            path="property_checks.py",
            function="assert_slugify_properties",
            cases=[],
            artifact_name="counterexample.json",
            regression_test_path="test_slugify_property_regression.py",
        ),
        counterexample={"input": "Hello  World", "message": "double separators"},
    )

    target = Path(path)
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "from property_checks import assert_slugify_properties" in content
    assert 'assert_slugify_properties("Hello  World")' in content


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


def test_hypothesis_check_generates_counterexample_and_regression_artifacts(tmp_path: Path) -> None:
    (tmp_path / "slugify.py").write_text(
        'def slugify(value: str) -> str:\n    return value.strip().lower().replace(" ", "-")\n',
        encoding="utf-8",
    )
    (tmp_path / "property_checks.py").write_text(
        "from slugify import slugify\n\n"
        "def assert_slugify_properties(value: str) -> None:\n"
        "    result = slugify(value)\n"
        '    assert "--" not in result, "slugify must collapse repeated separators"\n',
        encoding="utf-8",
    )

    task = TaskSpec(
        task_id="hypothesis_regression",
        title="Generate regression artifact from property case",
        prompt="noop",
        workspace=tmp_path,
        adapter="codex",
        allowed_files=["slugify.py"],
        oracles=[OracleSpec(name="oracle", kind="python", command="-c \"print('ok')\"")],
        tags=["python"],
        hypothesis={
            "path": "property_checks.py",
            "function": "assert_slugify_properties",
            "cases": ["Hello  World"],
            "artifact_name": "slugify_counterexample.json",
            "regression_test_path": "test_slugify_property_regression.py",
        },
    )

    artifact_dir = tmp_path / "artifacts"
    report = verify_workspace(
        tmp_path,
        task=task,
        changed_files=["slugify.py"],
        claimed_success=True,
        artifact_dir=artifact_dir,
    )

    assert report.verdict.value == "FALSIFIED"
    assert isinstance(report.counterexample, dict)
    assert report.counterexample["input"] == "Hello  World"
    by_name = {check.name: check for check in report.checks}
    assert by_name["hypothesis"].status.value == "failed"
    assert Path(by_name["hypothesis"].details["counterexample_artifact"]).exists()
    assert Path(by_name["hypothesis"].details["regression_test_artifact"]).exists()


def test_hypothesis_misconfiguration_returns_failed_check(tmp_path: Path) -> None:
    (tmp_path / "slugify.py").write_text(
        'def slugify(value: str) -> str:\n    return value.strip().lower().replace(" ", "-")\n',
        encoding="utf-8",
    )
    task = TaskSpec(
        task_id="hypothesis_misconfigured",
        title="Surface property checker configuration errors as verifier failures",
        prompt="noop",
        workspace=tmp_path,
        adapter="codex",
        allowed_files=["slugify.py"],
        oracles=[OracleSpec(name="oracle", kind="python", command="-c \"print('ok')\"")],
        tags=["python"],
        hypothesis={
            "path": "missing_property_checks.py",
            "function": "assert_slugify_properties",
            "cases": ["Hello  World"],
        },
    )

    report = verify_workspace(
        tmp_path,
        task=task,
        changed_files=["slugify.py"],
        claimed_success=True,
        artifact_dir=tmp_path / "artifacts",
    )

    assert report.verdict.value == "FALSIFIED"
    by_name = {check.name: check for check in report.checks}
    hypothesis = by_name["hypothesis"]
    assert hypothesis.status.value == "failed"
    assert hypothesis.exit_code == 1
    assert hypothesis.details["configuration_error"] is True
