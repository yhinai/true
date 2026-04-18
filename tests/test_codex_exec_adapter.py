from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cbc.config import CodexConfig
from cbc.model.codex_exec import CodexExecAdapter
from cbc.model.prompts import JSON_RESPONSE_CONTRACT, write_schema_file


def test_codex_exec_uses_stdin_prompt_and_parses_agent_message(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen["command"] = command
        seen["kwargs"] = kwargs
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
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

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
    assert kwargs["input"] == "return valid json"
    assert kwargs["cwd"] == workspace
    assert kwargs["text"] is True


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

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

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
