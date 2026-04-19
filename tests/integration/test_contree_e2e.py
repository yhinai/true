"""Opt-in end-to-end test for --sandbox=contree.

Skips cleanly when the ConTree SDK or backend is unavailable.
Run explicitly with: pytest tests/integration/ -m slow
"""

from __future__ import annotations

import subprocess

import pytest

# Skip the entire module if the SDK is not installed.
pytest.importorskip("contree_sdk")


@pytest.mark.slow
def test_calculator_bug_runs_under_contree():
    """Requires contree-sdk installed and a reachable ConTree backend."""
    result = subprocess.run(
        [
            "uv", "run", "cbc", "run",
            "fixtures/oracle_tasks/calculator_bug/task.yaml",
            "--mode=treatment",
            "--sandbox=contree",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )

    if result.returncode != 0:
        # Distinguish "backend unreachable" from real failures.
        combined = (result.stdout + result.stderr).lower()
        backend_unreachable_signals = (
            "connection refused",
            "no route to host",
            "name or service not known",
            "could not connect",
            "contree backend",
            "contree_url",
            "no valid authentication",
            "missing token",
        )
        if any(signal in combined for signal in backend_unreachable_signals):
            pytest.skip(f"ConTree backend unavailable: {combined[:500]}")
        pytest.fail(f"cbc run --sandbox=contree exited {result.returncode}\n"
                    f"stdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}")

    assert '"verdict"' in result.stdout or '"status"' in result.stdout
