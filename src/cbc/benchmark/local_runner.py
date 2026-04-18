from __future__ import annotations

from pathlib import Path

import yaml

from cbc.benchmark.compare import run_comparison
from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.models import BenchmarkComparison


def run_local_benchmark(config_path: Path, config: AppConfig = DEFAULT_CONFIG) -> BenchmarkComparison:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    task_paths = []
    for raw_path in payload["tasks"]:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (config_path.parent / candidate).resolve()
        else:
            candidate = candidate.resolve()
        task_paths.append(candidate)
    return run_comparison(task_paths=task_paths, config_path=config_path.resolve(), config=config)
