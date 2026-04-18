from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from cbc.benchmark.compare import run_comparison
from cbc.config import AppConfig, CodexConfig, DEFAULT_CONFIG
from cbc.models import BenchmarkComparison


class BenchmarkConfigFile(BaseModel):
    tasks: list[Path] = Field(default_factory=list)
    codex: CodexConfig | None = None


class ResolvedBenchmarkConfig(BaseModel):
    task_paths: list[Path]
    codex: CodexConfig | None = None


def load_benchmark_config(config_path: Path) -> ResolvedBenchmarkConfig:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "tasks" not in payload:
        raise ValueError(
            f"{config_path} must define a 'tasks' list. "
            "Legacy JSON scaffold configs are not valid for the replay smoke benchmark."
        )
    config = BenchmarkConfigFile.model_validate(payload)
    if not config.tasks:
        raise ValueError(f"{config_path} must define a non-empty 'tasks' list.")
    task_paths = []
    for raw_task in config.tasks:
        task_path = Path(raw_task)
        if not task_path.is_absolute():
            task_path = (config_path.parent / task_path).resolve()
        else:
            task_path = task_path.resolve()
        task_paths.append(task_path)
    return ResolvedBenchmarkConfig(task_paths=task_paths, codex=config.codex)


def load_task_paths_from_config(config_path: Path) -> list[Path]:
    return load_benchmark_config(config_path).task_paths


def apply_benchmark_config(config: AppConfig, benchmark_config: ResolvedBenchmarkConfig) -> AppConfig:
    if benchmark_config.codex is None:
        return config

    codex_overrides = benchmark_config.codex.model_dump(exclude_unset=True)
    if not codex_overrides:
        return config

    merged_codex = config.codex.model_copy(update=codex_overrides)
    return config.model_copy(deep=True, update={"codex": merged_codex})


def run_local_benchmark(config_path: Path, config: AppConfig = DEFAULT_CONFIG) -> BenchmarkComparison:
    benchmark_config = load_benchmark_config(config_path)
    effective_config = apply_benchmark_config(config, benchmark_config)
    return run_comparison(task_paths=benchmark_config.task_paths, config_path=config_path.resolve(), config=effective_config)
