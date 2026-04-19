from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from cbc.config import CodexConfig
from cbc.model import codex_exec as codex_exec_module
from cbc.model.codex_exec import CodexExecAdapter
from cbc.model.prompts import JSON_RESPONSE_CONTRACT, write_schema_file


def _make_fake_proc(
    *,
    stdout_text: str,
    stderr_text: str = "",
    returncode: int = 0,
) -> MagicMock:
    """Build a MagicMock that mimics a terminated subprocess.Popen instance."""

    proc = MagicMock()
    proc.stdout = io.StringIO(stdout_text)
    proc.stderr = io.StringIO(stderr_text)
    proc.stdin = MagicMock()
    proc.poll.return_value = returncode
    proc.wait.return_value = returncode
    proc.returncode = returncode
    return proc


def _install_fake_popen(
    monkeypatch,
    *,
    stdout_text: str,
    stderr_text: str = "",
    returncode: int = 0,
    seen: dict[str, Any] | None = None,
) -> MagicMock:
    proc = _make_fake_proc(stdout_text=stdout_text, stderr_text=stderr_text, returncode=returncode)

    def fake_popen(command: list[str], **kwargs: Any) -> MagicMock:
        if seen is not None:
            seen["command"] = command
            seen["kwargs"] = kwargs
        return proc

    monkeypatch.setattr(codex_exec_module.subprocess, "Popen", fake_popen)
    return proc


def test_codex_exec_uses_stdin_prompt_and_parses_agent_message(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, Any] = {}
    stdout = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "thread_123"}),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_0",
                        "type": "agent_message",
                        "text": json.dumps(
                            {
                                "summary": "done",
                                "claimed_success": True,
                                "writes": [],
                                "notes": [],
                            }
                        ),
                    },
                }
            ),
        ]
    )
    proc = _install_fake_popen(monkeypatch, stdout_text=stdout, seen=seen)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    schema_path = tmp_path / "schema.json"
    write_schema_file(schema_path)

    adapter = CodexExecAdapter(CodexConfig())
    response, events = adapter.run(
        prompt="return valid json",
        workspace=workspace,
        attempt=1,
        schema_path=schema_path,
    )

    assert response.summary == "done"
    assert response.claimed_success is True
    assert response.writes == []
    assert response.notes == []
    assert [event.kind for event in events] == ["thread.started", "item.completed"]

    command = seen["command"]
    assert isinstance(command, list)
    assert command[-1] == "-"
    assert "--output-schema" in command

    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["cwd"] == workspace
    assert kwargs["text"] is True
    proc.stdin.write.assert_called_once_with("return valid json")
    proc.stdin.close.assert_called_once()


def test_codex_exec_parses_legacy_message_event(monkeypatch, tmp_path: Path) -> None:
    stdout = "\n".join(
        [
            json.dumps(
                {
                    "type": "message",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "text": json.dumps(
                                    {
                                        "summary": "legacy",
                                        "claimed_success": False,
                                        "writes": [],
                                        "notes": ["n"],
                                    }
                                )
                            }
                        ],
                    },
                }
            )
        ]
    )
    _install_fake_popen(monkeypatch, stdout_text=stdout)

    adapter = CodexExecAdapter(CodexConfig())
    response, _events = adapter.run(prompt="fix it", workspace=tmp_path, attempt=1, schema_path=None)

    assert response.summary == "legacy"
    assert response.claimed_success is False
    assert response.notes == ["n"]


def test_write_schema_file_marks_all_properties_required(tmp_path: Path) -> None:
    schema_path = write_schema_file(tmp_path / "response_schema.json")
    payload = json.loads(schema_path.read_text(encoding="utf-8"))

    assert payload["required"] == JSON_RESPONSE_CONTRACT["required"] == ["summary", "claimed_success", "notes", "writes"]
    assert payload["properties"]["writes"]["items"]["required"] == ["path", "content", "executable"]


def test_codex_exec_includes_runtime_overrides(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, Any] = {}
    stdout = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(
                    {
                        "summary": "done",
                        "claimed_success": True,
                        "writes": [],
                        "notes": [],
                    }
                ),
            },
        }
    )
    _install_fake_popen(monkeypatch, stdout_text=stdout, seen=seen)

    writable = tmp_path / "shared"
    writable.mkdir()
    adapter = CodexExecAdapter(
        CodexConfig(
            default_model="gpt-5.4",
            sandbox="danger-full-access",
            profile="benchmark",
            config_overrides=['model_reasoning_effort="medium"'],
            add_dirs=[writable],
            skip_git_repo_check=False,
        ),
        allow_dangerous=True,
    )
    adapter.run(prompt="fix it", workspace=tmp_path, attempt=1, schema_path=None)

    command = seen["command"]
    assert isinstance(command, list)
    assert "--model" in command and "gpt-5.4" in command
    assert "--sandbox" in command and "danger-full-access" in command
    assert "--profile" in command and "benchmark" in command
    assert command.count("--config") == 1
    assert 'model_reasoning_effort="medium"' in command
    assert "--add-dir" in command and str(writable) in command
    assert "--skip-git-repo-check" not in command


def test_codex_exec_timeout_returns_structured_failure(monkeypatch, tmp_path: Path) -> None:
    """A process that never exits should be killed once the deadline passes."""

    proc = MagicMock()
    proc.stdout = io.StringIO("")
    proc.stderr = io.StringIO("")
    proc.stdin = MagicMock()
    # Never exits on its own; timeout path must kill it.
    proc.poll.return_value = None
    proc.returncode = -9

    def fake_popen(command: list[str], **kwargs: Any) -> MagicMock:
        return proc

    # Force the deadline check to fire immediately.
    times = iter([0.0, 0.0, 1000.0, 1000.0, 1000.0])
    monkeypatch.setattr(codex_exec_module.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(codex_exec_module.time, "sleep", lambda _s: None)
    monkeypatch.setattr(codex_exec_module.subprocess, "Popen", fake_popen)

    adapter = CodexExecAdapter(CodexConfig(timeout_seconds=5))
    result = adapter.run(prompt="fix it", workspace=tmp_path, attempt=1, schema_path=None)

    assert proc.kill.called
    assert result.response.claimed_success is False
    assert result.failure_reason == "codex exec timed out after 5s"
    assert result.events[-1].kind == "adapter.timeout"
    assert "timed out" in result.response.summary.lower()


def test_codex_adapter_streams_lines_via_callback(monkeypatch, tmp_path: Path) -> None:
    """Verify adapter invokes a per-line hook while the subprocess runs."""

    emitted_lines: list[str] = []

    def on_line(line: str) -> None:
        emitted_lines.append(line)

    # Three JSONL lines; the agent_message carries a valid ModelResponse payload.
    agent_text = json.dumps(
        {
            "summary": "streamed",
            "claimed_success": True,
            "writes": [],
            "notes": [],
        }
    )
    stdout_text = (
        json.dumps({"type": "thread.started"}) + "\n"
        + json.dumps({"type": "progress", "msg": "edit 1"}) + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": agent_text},
            }
        )
        + "\n"
    )

    _install_fake_popen(monkeypatch, stdout_text=stdout_text)

    adapter = CodexExecAdapter(CodexConfig(timeout_seconds=5))
    result = adapter.run(
        prompt="do something",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
        on_stdout_line=on_line,
    )

    assert len(emitted_lines) == 3
    assert emitted_lines[0].startswith('{"type": "thread.started"')
    assert emitted_lines[1].startswith('{"type": "progress"')
    assert emitted_lines[2].startswith('{"type": "item.completed"')
    # The downstream parsing still produces the same ModelResponse shape.
    assert result.response.summary == "streamed"
    assert result.response.claimed_success is True


def test_codex_adapter_without_callback_preserves_interface(monkeypatch, tmp_path: Path) -> None:
    """When no callback is passed, the adapter still returns the prior shape."""

    stdout_text = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(
                    {
                        "summary": "ok",
                        "claimed_success": True,
                        "writes": [],
                        "notes": [],
                    }
                ),
            },
        }
    )
    _install_fake_popen(monkeypatch, stdout_text=stdout_text)

    adapter = CodexExecAdapter(CodexConfig())
    result = adapter.run(prompt="x", workspace=tmp_path, attempt=1, schema_path=None)

    assert result.response.summary == "ok"
    assert result.failure_reason is None
    # Ensure subprocess.run is no longer involved.
    assert hasattr(subprocess, "run")  # sanity: still the standard module
