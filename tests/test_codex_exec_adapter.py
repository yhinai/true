from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cbc.config import CodexConfig
from cbc.model.codex_exec import CodexExecAdapter
from cbc.model.prompts import JSON_RESPONSE_CONTRACT


def test_codex_exec_parses_current_item_completed_event(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"t"}',
            '{"type":"turn.started"}',
            '{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"{\\"summary\\":\\"ok\\",\\"claimed_success\\":true,\\"writes\\":[],\\"notes\\":[]}"}}',
            '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}',
        ]
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = CodexExecAdapter(CodexConfig())
    response, events = adapter.run(prompt="fix it", workspace=tmp_path, attempt=1, schema_path=None)

    assert response.summary == "ok"
    assert response.claimed_success is True
    assert response.writes == []
    assert [event.kind for event in events] == ["thread.started", "turn.started", "item.completed", "turn.completed"]


def test_codex_exec_parses_legacy_message_event(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    stdout = "\n".join(
        [
            '{"type":"message","message":{"role":"assistant","content":[{"text":"{\\"summary\\":\\"legacy\\",\\"claimed_success\\":false,\\"writes\\":[],\\"notes\\":[\\"n\\"]}"}]}}'
        ]
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    adapter = CodexExecAdapter(CodexConfig())
    response, _events = adapter.run(prompt="fix it", workspace=tmp_path, attempt=1, schema_path=None)

    assert response.summary == "legacy"
    assert response.claimed_success is False
    assert response.notes == ["n"]


def test_output_schema_requires_all_declared_fields() -> None:
    assert JSON_RESPONSE_CONTRACT["required"] == ["summary", "claimed_success", "notes", "writes"]
    write_item = JSON_RESPONSE_CONTRACT["properties"]["writes"]["items"]
    assert write_item["required"] == ["path", "content", "executable"]
