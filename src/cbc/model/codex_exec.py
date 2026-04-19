from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from cbc.config import CodexConfig
from cbc.model.adapter import ModelAdapter
from cbc.model.events import text_event
from cbc.models import AdapterRunResult, ModelEvent, ModelResponse, ModelUsage


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
        candidate_index: int = 0,
        candidate_role: str = "primary",
        schema_path: Path | None = None,
    ) -> AdapterRunResult:
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

        stdout = ""
        stderr = ""
        return_code = 1
        timeout_reason: str | None = None
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout_seconds,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            return_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            timeout_reason = (
                f"codex exec timed out after {self.config.timeout_seconds}s"
            )

        parsed = _parse_codex_output(stdout)
        events = parsed["events"]
        parsed_message = parsed["parsed_message"]
        reported_error = parsed["reported_error"]
        usage = _estimate_usage(events, config=self.config)

        if timeout_reason is not None:
            events.append(text_event("adapter.timeout", timeout_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=timeout_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[timeout_reason],
                ),
                events=events,
                usage=usage,
                failure_reason=timeout_reason,
            )

        if return_code != 0 and not parsed_message:
            failure_reason = (
                reported_error
                or stderr.strip()
                or "codex exec failed without a final assistant message"
            )
            events.append(text_event("adapter.failed", failure_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=failure_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[failure_reason],
                ),
                events=events,
                usage=usage,
                failure_reason=failure_reason,
            )

        if not parsed_message:
            failure_reason = "codex exec did not produce a parseable assistant message"
            events.append(text_event("adapter.failed", failure_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=failure_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[failure_reason],
                ),
                events=events,
                usage=usage,
                failure_reason=failure_reason,
            )

        try:
            response = ModelResponse.model_validate_json(parsed_message)
        except ValidationError as exc:
            failure_reason = f"codex exec produced invalid JSON output: {exc}"
            events.append(text_event("adapter.failed", failure_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=failure_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[failure_reason],
                ),
                events=events,
                usage=usage,
                failure_reason=failure_reason,
            )
        return AdapterRunResult(response=response, events=events, usage=usage)


def _parse_codex_output(stdout: str) -> dict[str, Any]:
    events: list[ModelEvent] = []
    parsed_message: str | None = None
    reported_error: str | None = None
    for line in stdout.splitlines():
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
    return {
        "events": events,
        "parsed_message": parsed_message,
        "reported_error": reported_error,
    }


def _estimate_usage(events: list[ModelEvent], *, config: CodexConfig) -> ModelUsage:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    for event in events:
        payload = event.payload
        prompt_tokens += _extract_int(payload, "prompt_tokens", "input_tokens")
        completion_tokens += _extract_int(payload, "completion_tokens", "output_tokens")
        total_tokens += _extract_int(payload, "total_tokens")
        usage = payload.get("usage")
        if isinstance(usage, dict):
            prompt_tokens += _extract_int(usage, "prompt_tokens", "input_tokens")
            completion_tokens += _extract_int(usage, "completion_tokens", "output_tokens")
            total_tokens += _extract_int(usage, "total_tokens")
    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens
    estimated_cost_usd: float | None = None
    if config.prompt_token_cost_per_1k is not None and config.completion_token_cost_per_1k is not None:
        estimated_cost_usd = (
            (prompt_tokens / 1000) * config.prompt_token_cost_per_1k
            + (completion_tokens / 1000) * config.completion_token_cost_per_1k
        )
    return ModelUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )


def _extract_int(payload: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return 0


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
