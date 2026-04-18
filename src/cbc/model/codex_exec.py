from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from cbc.config import CodexConfig
from cbc.model.adapter import ModelAdapter
from cbc.models import ModelEvent, ModelResponse


class CodexExecAdapter(ModelAdapter):
    name = "codex"

    def __init__(self, config: CodexConfig) -> None:
        self.config = config

    def run(
        self,
        *,
        prompt: str,
        workspace: Path,
        attempt: int,
        schema_path: Path | None = None,
    ) -> tuple[ModelResponse, list[ModelEvent]]:
        command = [
            self.config.executable,
            "exec",
            "--json",
            "--cd",
            str(workspace),
            "--sandbox",
            self.config.sandbox,
        ]
        if self.config.skip_git_repo_check:
            command.append("--skip-git-repo-check")
        if self.config.default_model:
            command.extend(["--model", self.config.default_model])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        for override in self.config.config_overrides:
            command.extend(["--config", override])
        for add_dir in self.config.add_dirs:
            command.extend(["--add-dir", str(add_dir)])
        if self.config.dangerously_bypass_approvals:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        if schema_path:
            command.extend(["--output-schema", str(schema_path)])
        command.append("-")

        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            capture_output=True,
            text=True,
            check=False,
        )

        events: list[ModelEvent] = []
        parsed_message: str | None = None
        reported_error: str | None = None
        for line in completed.stdout.splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(ModelEvent(kind=payload.get("type", "event"), payload=payload))
            candidate = _extract_assistant_message(payload)
            if candidate:
                parsed_message = candidate
            if payload.get("type") == "error":
                reported_error = payload.get("message")
            elif payload.get("type") == "turn.failed":
                reported_error = payload.get("error", {}).get("message", reported_error)

        if completed.returncode != 0 and not parsed_message:
            raise RuntimeError(
                reported_error
                or completed.stderr.strip()
                or "codex exec failed without a final assistant message"
            )

        if not parsed_message:
            raise RuntimeError("codex exec did not produce a parseable assistant message")

        try:
            response = ModelResponse.model_validate_json(parsed_message)
        except ValidationError as exc:
            raise RuntimeError(f"codex exec produced invalid JSON output: {exc}") from exc
        return response, events


def _extract_assistant_message(payload: dict[str, Any]) -> str | None:
    if payload.get("type") == "item.completed":
        item = payload.get("item", {})
        if isinstance(item, dict) and item.get("type") == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                return text

    if payload.get("type") == "message":
        message = payload.get("message", {})
        if isinstance(message, dict) and message.get("role") == "assistant":
            content = message.get("content", [])
            if isinstance(content, list) and content:
                last = content[-1]
                if isinstance(last, dict):
                    text = last.get("text")
                    if isinstance(text, str):
                        return text
                if isinstance(last, str):
                    return last

    return None
