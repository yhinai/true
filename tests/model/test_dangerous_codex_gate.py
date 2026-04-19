from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from cbc.config import CodexConfig
from cbc.model import codex_exec as codex_exec_module
from cbc.model.codex_exec import CodexExecAdapter


def _install_fake_popen(monkeypatch, *, stdout_text: str) -> None:
    proc = MagicMock()
    proc.stdout = io.StringIO(stdout_text)
    proc.stderr = io.StringIO("")
    proc.stdin = MagicMock()
    proc.poll.return_value = 0
    proc.wait.return_value = 0
    proc.returncode = 0

    def fake_popen(command: list[str], **kwargs: Any) -> MagicMock:
        return proc

    monkeypatch.setattr(codex_exec_module.subprocess, "Popen", fake_popen)


def test_dangerous_bypass_without_gate_raises() -> None:
    config = CodexConfig(dangerously_bypass_approvals=True)
    with pytest.raises(ValueError, match="--allow-dangerous-codex"):
        CodexExecAdapter(config)


def test_danger_full_access_sandbox_without_gate_raises() -> None:
    config = CodexConfig(sandbox="danger-full-access")
    with pytest.raises(ValueError, match="--allow-dangerous-codex"):
        CodexExecAdapter(config)


def test_safe_config_does_not_raise() -> None:
    adapter = CodexExecAdapter(CodexConfig())
    assert adapter.config.sandbox == "workspace-write"


def test_dangerous_with_gate_proceeds_and_logs_warning(
    monkeypatch, tmp_path: Path, caplog
) -> None:
    import logging

    agent_text = json.dumps(
        {
            "summary": "done",
            "claimed_success": True,
            "writes": [],
            "notes": [],
        }
    )
    stdout = json.dumps(
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": agent_text},
        }
    )
    _install_fake_popen(monkeypatch, stdout_text=stdout)

    config = CodexConfig(
        dangerously_bypass_approvals=True,
        sandbox="danger-full-access",
    )
    with caplog.at_level(logging.WARNING, logger="cbc.model.codex_exec"):
        adapter = CodexExecAdapter(config, allow_dangerous=True, task_id="risky-task")

    assert any(
        "sandbox bypass" in rec.message and "risky-task" in rec.message
        for rec in caplog.records
    )

    result = adapter.run(prompt="fix", workspace=tmp_path, attempt=1, schema_path=None)
    assert result.response.summary == "done"
    assert result.failure_reason is None
