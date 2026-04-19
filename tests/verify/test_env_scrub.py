from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cbc.verify.env_utils import (
    PRESERVED_KEYS,
    SENSITIVE_KEYS,
    SENSITIVE_PREFIXES,
    scrub_env,
)
from cbc.verify.lint_runner import run_lint


@pytest.mark.parametrize("prefix", list(SENSITIVE_PREFIXES))
def test_scrub_env_drops_all_prefixes(prefix: str) -> None:
    key = f"{prefix}ANYTHING"
    base = {key: "secret", "PATH": "/bin"}
    scrubbed = scrub_env(base)
    assert key not in scrubbed
    assert scrubbed["PATH"] == "/bin"


@pytest.mark.parametrize("key", list(SENSITIVE_KEYS))
def test_scrub_env_drops_bare_keys(key: str) -> None:
    base = {key: "secret", "PATH": "/bin"}
    scrubbed = scrub_env(base)
    assert key not in scrubbed
    assert scrubbed["PATH"] == "/bin"


def test_scrub_env_preserves_baseline_keys() -> None:
    base = {
        "PATH": "/bin",
        "HOME": "/home/user",
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "LC_CTYPE": "UTF-8",
        "UNRELATED": "kept",
    }
    scrubbed = scrub_env(base)
    for key in PRESERVED_KEYS:
        assert scrubbed[key] == base[key]
    assert scrubbed["LC_ALL"] == "C.UTF-8"
    assert scrubbed["LC_CTYPE"] == "UTF-8"
    assert scrubbed["UNRELATED"] == "kept"


def test_scrub_env_strips_representative_secrets() -> None:
    base = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_ANON_KEY": "anon",
        "VERCEL_TOKEN": "v",
        "OPENAI_API_KEY": "sk-xxx",
        "ANTHROPIC_API_KEY": "sk-ant",
        "GITHUB_TOKEN": "ghp_xxx",
        "POSTGRES_URL": "postgres://",
        "AWS_ACCESS_KEY_ID": "AKIA",
        "PGPASSWORD": "pw",
        "DATABASE_URL": "postgres://",
        "PATH": "/bin",
    }
    scrubbed = scrub_env(base)
    for key in base:
        if key == "PATH":
            assert scrubbed[key] == "/bin"
        else:
            assert key not in scrubbed


def test_scrub_env_returns_copy() -> None:
    base = {"PATH": "/bin", "OPENAI_API_KEY": "sk"}
    scrubbed = scrub_env(base)
    scrubbed["PATH"] = "/usr/bin"
    assert base["PATH"] == "/bin"


def test_run_lint_does_not_leak_supabase_env(tmp_path: Path) -> None:
    """Verify that a runner called with tainted env does not leak secrets to the child."""
    captured: dict[str, object] = {}

    real_run = subprocess.run

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        # Return a minimal completed process to keep downstream code happy.
        return real_run(
            [sys.executable, "-c", "print('ok')"],
            capture_output=True,
            text=True,
            check=False,
        )

    tainted_env = {
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_ANON_KEY": "anon",
        "OPENAI_API_KEY": "sk-xxx",
        "PATH": os.environ.get("PATH", "/bin"),
    }

    with patch.dict(os.environ, tainted_env, clear=True), patch(
        "cbc.verify.lint_runner.subprocess.run", side_effect=fake_run
    ):
        run_lint(tmp_path)

    child_env = captured["env"]
    assert isinstance(child_env, dict)
    assert "SUPABASE_URL" not in child_env
    assert "SUPABASE_ANON_KEY" not in child_env
    assert "OPENAI_API_KEY" not in child_env
    assert child_env.get("PATH") == tainted_env["PATH"]
    # PYTHONDONTWRITEBYTECODE should still be injected.
    assert child_env.get("PYTHONDONTWRITEBYTECODE") == "1"
    # Command must be a list (shell=False path).
    assert isinstance(captured["cmd"], list)
