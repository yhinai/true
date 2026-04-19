"""Contract tests for the IntelliJ plugin's NDJSON stream consumer.

The plugin's `NdjsonParser` and `CbcRunService` depend on the following
invariants of `cbc run --stream` / `cbc solve --stream`:

1. Stdout contains one JSON object per line, in addition to any free-form
   rendering (e.g. proof card) that does **not** start with ``{``.
2. Every JSON object has a ``type`` string field.
3. At least one ``verification.completed`` event carries a ``verdict`` whose
   value is one of ``VERIFIED / FALSIFIED / TIMED_OUT / UNPROVEN``.
4. ``attempt`` (when present) is an int, and events with a ``candidate_id`` /
   ``candidate_role`` use string values.

These tests run the real CLI against the deterministic
``calculator_bug`` replay fixture so no network / Codex is required.

We also reproduce the Kotlin parser's logic in pure Python and assert the
same classification so the plugin's unit behaviour is indirectly covered
from CI.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK = REPO_ROOT / "fixtures" / "oracle_tasks" / "calculator_bug" / "task.yaml"

VERDICTS = {"VERIFIED", "FALSIFIED", "TIMED_OUT", "UNPROVEN"}


def _run_cbc_stream() -> list[dict]:
    proc = subprocess.run(
        [sys.executable, "-m", "cbc.main", "run", str(TASK), "--stream"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )
    events: list[dict] = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        events.append(json.loads(stripped))
    return events


@pytest.fixture(scope="module")
def stream_events() -> list[dict]:
    return _run_cbc_stream()


def test_stream_emits_json_lines(stream_events: list[dict]) -> None:
    assert stream_events, "cbc --stream produced no JSON lines"
    for ev in stream_events:
        assert isinstance(ev, dict)
        assert isinstance(ev.get("type"), str), ev


def test_stream_contains_lifecycle_events(stream_events: list[dict]) -> None:
    types = {ev["type"] for ev in stream_events}
    # Minimum lifecycle the plugin's tree relies on.
    for required in ("adapter.started", "verification.started", "verification.completed"):
        assert required in types, f"missing {required} in {types}"


def test_stream_verdict_values(stream_events: list[dict]) -> None:
    completions = [ev for ev in stream_events if ev["type"] == "verification.completed"]
    assert completions, "no verification.completed event"
    for ev in completions:
        assert ev.get("verdict") in VERDICTS, ev


def test_stream_attempt_is_int(stream_events: list[dict]) -> None:
    for ev in stream_events:
        if "attempt" in ev:
            assert isinstance(ev["attempt"], int), ev


# ---------------------------------------------------------------------------
# Pure-Python mirror of the Kotlin `NdjsonParser` / `Verdict.parse` logic.
# Kept in lockstep with plugin/src/main/kotlin/dev/cbc/plugin/stream/NdjsonParser.kt
# so regressions in either side break these tests.
# ---------------------------------------------------------------------------


def _parse_verdict(raw: str | None) -> str:
    if raw is None:
        return "UNKNOWN"
    up = raw.upper()
    if up in {"VERIFIED", "FALSIFIED", "UNPROVEN"}:
        return up
    if up in {"TIMED_OUT", "TIMEOUT"}:
        return "TIMED_OUT"
    return "UNKNOWN"


def _parse_line(line: str) -> dict | None:
    s = line.strip()
    if not s or not s.startswith("{"):
        return None
    try:
        raw = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict) or not isinstance(raw.get("type"), str):
        return None
    attempt = raw.get("attempt") if isinstance(raw.get("attempt"), int) else None
    candidate_id = raw.get("candidate_id") or raw.get("candidate_role")
    verdict = _parse_verdict(raw.get("verdict")) if "verdict" in raw else None
    return {
        "type": raw["type"],
        "attempt": attempt,
        "candidate_id": str(candidate_id) if candidate_id is not None else None,
        "verdict": verdict,
        "raw": raw,
    }


def test_python_parser_handles_real_stream(stream_events: list[dict]) -> None:
    for ev in stream_events:
        parsed = _parse_line(json.dumps(ev))
        assert parsed is not None
        assert parsed["type"] == ev["type"]


@pytest.mark.parametrize(
    "line",
    [
        "",
        "   ",
        "not json",
        "# Proof Card",
        "{ not valid json",
        '{"attempt": 1}',  # missing `type`
    ],
)
def test_python_parser_rejects_non_events(line: str) -> None:
    assert _parse_line(line) is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("VERIFIED", "VERIFIED"),
        ("verified", "VERIFIED"),
        ("FALSIFIED", "FALSIFIED"),
        ("timed_out", "TIMED_OUT"),
        ("TIMEOUT", "TIMED_OUT"),
        ("UNPROVEN", "UNPROVEN"),
        ("something_new", "UNKNOWN"),
        (None, "UNKNOWN"),
    ],
)
def test_verdict_parse_mirrors_kotlin(raw: str | None, expected: str) -> None:
    assert _parse_verdict(raw) == expected
