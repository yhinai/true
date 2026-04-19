from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolchainDetection:
    languages: list[str]
    verify_commands: list[str]
    lint_command: str | None = None
    typecheck_command: str | None = None


def detect_toolchain(workspace: Path) -> ToolchainDetection:
    languages: list[str] = []
    verify_commands: list[str] = []
    lint_command: str | None = None
    typecheck_command: str | None = None

    package_json = workspace / "package.json"
    if package_json.exists():
        languages.append("javascript")
        verify_commands.append("npm test")
        scripts = _load_package_scripts(package_json)
        if "lint" in scripts:
            lint_command = "npm run lint"
        if "typecheck" in scripts:
            typecheck_command = "npm run typecheck"

    cargo_toml = workspace / "Cargo.toml"
    if cargo_toml.exists():
        languages.append("rust")
        verify_commands.append("cargo test")
        if lint_command is None:
            lint_command = "cargo fmt --check"
        if typecheck_command is None:
            typecheck_command = "cargo check"

    go_mod = workspace / "go.mod"
    if go_mod.exists():
        languages.append("go")
        verify_commands.append("go test ./...")

    python_markers = (
        workspace / "pyproject.toml",
        workspace / "pytest.ini",
        workspace / "setup.py",
        workspace / "requirements.txt",
    )
    has_python = any(marker.exists() for marker in python_markers) or any(workspace.rglob("test_*.py"))
    if has_python:
        languages.append("python")
        if any(workspace.rglob("test_*.py")):
            verify_commands.append("pytest -q")
        if lint_command is None:
            lint_command = "python3 -m compileall ."
        if typecheck_command is None and (workspace / "mypy.ini").exists():
            typecheck_command = "mypy ."

    deduped_languages = list(dict.fromkeys(languages))
    deduped_verify = list(dict.fromkeys(verify_commands))
    return ToolchainDetection(
        languages=deduped_languages,
        verify_commands=deduped_verify,
        lint_command=lint_command,
        typecheck_command=typecheck_command,
    )


def _load_package_scripts(package_json: Path) -> dict[str, str]:
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = payload.get("scripts")
    return scripts if isinstance(scripts, dict) else {}
