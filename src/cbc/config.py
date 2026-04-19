from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]


class PathsConfig(BaseModel):
    root: Path = Field(default_factory=lambda: Path.cwd())
    artifacts_dir: Path = Field(default_factory=lambda: Path.cwd() / "artifacts")
    reports_dir: Path = Field(default_factory=lambda: Path.cwd() / "reports")
    prompts_dir: Path = Field(default_factory=lambda: Path.cwd() / "prompts")
    benchmark_config_dir: Path = Field(default_factory=lambda: Path.cwd() / "benchmark-configs")
    storage_db: Path = Field(default_factory=lambda: Path.cwd() / "artifacts" / "cbc.sqlite3")


class RetryConfig(BaseModel):
    max_attempts: int = 2
    stop_on_unproven: bool = False


class ControllerBudgetConfig(BaseModel):
    max_model_calls_per_run: int = 4
    max_candidates_first_attempt: int = 2
    allow_alternate_candidates_on_retry: bool = False


class ControllerConfig(BaseModel):
    mode: Literal["sequential", "gearbox"] = "sequential"
    budget: ControllerBudgetConfig = Field(default_factory=ControllerBudgetConfig)


class CodexConfig(BaseModel):
    executable: str = "codex"
    default_model: str | None = None
    sandbox: SandboxMode = "workspace-write"
    profile: str | None = None
    config_overrides: list[str] = Field(default_factory=list)
    add_dirs: list[Path] = Field(default_factory=list)
    skip_git_repo_check: bool = True
    dangerously_bypass_approvals: bool = False
    timeout_seconds: int = 300
    prompt_token_cost_per_1k: float | None = None
    completion_token_cost_per_1k: float | None = None


class AppConfig(BaseModel):
    paths: PathsConfig = Field(default_factory=PathsConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    controller: ControllerConfig = Field(default_factory=ControllerConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)


DEFAULT_CONFIG = AppConfig()
