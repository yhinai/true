from __future__ import annotations

from pathlib import Path

from cbc.examples_refresh import _normalize_string, _normalize_text_content


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_normalize_string_scrubs_repo_and_temp_paths() -> None:
    source_root = REPO_ROOT / "artifacts" / "runs" / "abc123def456"
    value = (
        f"{source_root}/scheduler_trace.json "
        f"{REPO_ROOT}/fixtures/oracle_tasks/calculator_bug/workspace "
        "/var/folders/xx/tmp/cbc-workspace-abcd1234/workspace"
    )

    normalized = _normalize_string(
        value,
        source_root=source_root,
        repo_root=REPO_ROOT,
        example_dir=Path("artifacts/examples/calculator_treatment"),
    )

    assert "artifacts/examples/calculator_treatment/scheduler_trace.json" in normalized
    assert "<repo>/fixtures/oracle_tasks/calculator_bug/workspace" in normalized
    assert "<staged_workspace>" in normalized
    assert str(REPO_ROOT) not in normalized


def test_normalize_text_content_scrubs_transient_ids() -> None:
    content = (
        "# Proof Card\n\n"
        "- Run ID: `81409528ee07`\n"
        f"- Artifact Dir: `{REPO_ROOT}/artifacts/runs/07f4ff5258ba`\n"
    )

    normalized = _normalize_text_content(
        content,
        source_root=REPO_ROOT / "artifacts" / "runs" / "07f4ff5258ba",
        repo_root=REPO_ROOT,
        example_id="example-calculator-treatment",
        example_dir=Path("artifacts/examples/calculator_treatment"),
    )

    assert "`example-calculator-treatment`" in normalized
    assert "artifacts/examples/calculator_treatment" in normalized
    assert str(REPO_ROOT) not in normalized


def test_normalize_string_supports_expanded_benchmark_example_paths() -> None:
    source_root = REPO_ROOT / "reports" / "benchmarks" / "abc123def456"
    normalized = _normalize_string(
        f"{source_root}/comparison.json",
        source_root=source_root,
        repo_root=REPO_ROOT,
        example_dir=Path("reports/examples/expanded_benchmark"),
    )

    assert normalized == "reports/examples/expanded_benchmark/comparison.json"
