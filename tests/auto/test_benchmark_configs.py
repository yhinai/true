"""Every benchmark-configs/*.yaml must parse to a known schema."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

BENCH_ROOT = Path(__file__).resolve().parents[2] / "benchmark-configs"
BENCH_YAMLS = sorted(BENCH_ROOT.glob("*.yaml"))


@pytest.mark.parametrize(
    "bench_yaml",
    BENCH_YAMLS,
    ids=[p.stem for p in BENCH_YAMLS] or ["no-benchmarks"],
)
def test_benchmark_config_parses(bench_yaml: Path) -> None:
    data = yaml.safe_load(bench_yaml.read_text())
    assert isinstance(data, dict), f"{bench_yaml} must be a mapping at top level"
    # Required by cbc.benchmark.local_runner.load_benchmark_config.
    assert "tasks" in data, f"{bench_yaml.name} missing required key: tasks"
    tasks = data["tasks"]
    assert isinstance(tasks, list) and tasks, (
        f"{bench_yaml.name} 'tasks' must be a non-empty list"
    )
