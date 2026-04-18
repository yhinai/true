from __future__ import annotations

from pathlib import Path

import yaml

from cbc.benchmark.compare import run_comparison
from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.models import BenchmarkComparison


def load_task_paths_from_config(config_path: Path) -> list[Path]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "tasks" not in payload:
        raise ValueError(
            f"{config_path} must define a 'tasks' list. "
            "Legacy JSON scaffold configs are not valid for the replay smoke benchmark."
        )
    raw_tasks = payload["tasks"]
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError(f"{config_path} must define a non-empty 'tasks' list.")
    task_paths = []
    for raw_task in raw_tasks:
        task_path = Path(raw_task)
        if not task_path.is_absolute():
            task_path = (config_path.parent / task_path).resolve()
        else:
            task_path = task_path.resolve()
        task_paths.append(task_path)
    return task_paths


def run_local_benchmark(config_path: Path, config: AppConfig = DEFAULT_CONFIG) -> BenchmarkComparison:
    task_paths = load_task_paths_from_config(config_path)
    return run_comparison(task_paths=task_paths, config_path=config_path.resolve(), config=config)
