from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from cbc.benchmark.compare import run_comparison
from cbc.benchmark.controller_compare import run_controller_comparison
from cbc.config import AppConfig, CodexConfig, ControllerConfig, DEFAULT_CONFIG
from cbc.models import BenchmarkComparison, ControllerBenchmarkComparison


class BenchmarkConfigFile(BaseModel):
    tasks: list[Path] = Field(default_factory=list)
    codex: CodexConfig | None = None
    controller: ControllerConfig | None = None


class ResolvedBenchmarkConfig(BaseModel):
    task_paths: list[Path]
    codex: CodexConfig | None = None
    controller: ControllerConfig | None = None


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
    return ResolvedBenchmarkConfig(task_paths=task_paths, codex=config.codex, controller=config.controller)


def load_task_paths_from_config(config_path: Path) -> list[Path]:
    return load_benchmark_config(config_path).task_paths


def apply_benchmark_config(config: AppConfig, benchmark_config: ResolvedBenchmarkConfig) -> AppConfig:
    updates: dict[str, object] = {}
    if benchmark_config.codex is not None:
        codex_overrides = benchmark_config.codex.model_dump(exclude_unset=True)
        if codex_overrides:
            updates["codex"] = config.codex.model_copy(update=codex_overrides)
    if benchmark_config.controller is not None:
        controller_overrides = benchmark_config.controller.model_dump(exclude_unset=True)
        if controller_overrides:
            budget_overrides = controller_overrides.pop("budget", None)
            if isinstance(budget_overrides, dict):
                controller_overrides["budget"] = config.controller.budget.model_copy(update=budget_overrides)
            updates["controller"] = config.controller.model_copy(update=controller_overrides)
    if not updates:
        return config
    return config.model_copy(deep=True, update=updates)


def run_local_benchmark(config_path: Path, config: AppConfig = DEFAULT_CONFIG) -> BenchmarkComparison:
    benchmark_config = load_benchmark_config(config_path)
    effective_config = apply_benchmark_config(config, benchmark_config)
    return run_comparison(task_paths=benchmark_config.task_paths, config_path=config_path.resolve(), config=effective_config)


def run_local_controller_benchmark(
    config_path: Path,
    config: AppConfig = DEFAULT_CONFIG,
) -> ControllerBenchmarkComparison:
    benchmark_config = load_benchmark_config(config_path)
    effective_config = apply_benchmark_config(config, benchmark_config)
    return run_controller_comparison(
        task_paths=benchmark_config.task_paths,
        config_path=config_path.resolve(),
        config=effective_config,
    )
