from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cbc.graph.mismatch import detect_bounded_signature_mismatches
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
