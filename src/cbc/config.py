from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


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


class CodexConfig(BaseModel):
    executable: str = "codex"
    default_model: str | None = None
    sandbox: str = "workspace-write"
    skip_git_repo_check: bool = True
    dangerously_bypass_approvals: bool = False


class AppConfig(BaseModel):
    paths: PathsConfig = Field(default_factory=PathsConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)


DEFAULT_CONFIG = AppConfig()
