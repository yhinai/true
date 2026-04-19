from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from cbc.config import GeminiConfig
from cbc.model.gemini_exec import GeminiAdapter
from cbc.model.prompts import write_schema_file


def _make_fake_client(
    *,
    text: str,
    usage: dict[str, int] | None = None,
    raise_on_generate: Exception | None = None,
) -> tuple[MagicMock, dict[str, Any]]:
    """Return a fake google.genai.Client that captures the last call."""

    seen: dict[str, Any] = {}
    client = MagicMock()

    def fake_generate_content(
        *,
        model: str,
        contents: str,
        config: Any,
    ) -> Any:
        seen["model"] = model
        seen["contents"] = contents
        seen["config"] = config
        if raise_on_generate is not None:
            raise raise_on_generate
        usage_meta = None
        if usage is not None:
            usage_meta = SimpleNamespace(
                prompt_token_count=usage.get("prompt_token_count", 0),
                candidates_token_count=usage.get("candidates_token_count", 0),
                total_token_count=usage.get("total_token_count", 0),
            )
        return SimpleNamespace(text=text, usage_metadata=usage_meta)

    client.models.generate_content = fake_generate_content
    return client, seen


def test_gemini_adapter_success_path(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "summary": "fixed it",
            "claimed_success": True,
            "writes": [
                {"path": "foo.py", "content": "print('hi')", "executable": False},
            ],
            "notes": ["patched the bug"],
        }
    )
    usage = {
        "prompt_token_count": 123,
        "candidates_token_count": 45,
        "total_token_count": 168,
    }
    client, seen = _make_fake_client(text=payload, usage=usage)

    schema_path = write_schema_file(tmp_path / "schema.json")
    adapter = GeminiAdapter(GeminiConfig(), client=client)
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=schema_path,
    )

    assert result.failure_reason is None
    assert result.response.summary == "fixed it"
    assert result.response.claimed_success is True
    assert len(result.response.writes) == 1
    assert result.response.writes[0].path == "foo.py"
    assert result.response.notes == ["patched the bug"]

    # Usage mirrors the SDK metadata.
    assert result.usage.prompt_tokens == 123
    assert result.usage.completion_tokens == 45
    assert result.usage.total_tokens == 168

    # The prompt should have been augmented with the schema.
    assert "please fix" in seen["contents"]
    assert "\"summary\"" in seen["contents"]
    assert seen["model"] == GeminiConfig().default_model

    # Observability events are emitted.
    kinds = [event.kind for event in result.events]
    assert "adapter.prompt" in kinds
    assert "adapter.raw_response" in kinds
    assert "adapter.usage" in kinds


def test_gemini_adapter_invalid_json_sets_failure_reason(tmp_path: Path) -> None:
    client, _ = _make_fake_client(text="not valid json")
    adapter = GeminiAdapter(GeminiConfig(), client=client)
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
    )

    assert result.failure_reason is not None
    assert "invalid JSON" in result.failure_reason or "non-JSON" in result.failure_reason
    assert result.response.claimed_success is False
    assert result.events[-1].kind == "adapter.failed"


def test_gemini_adapter_empty_response_sets_failure_reason(tmp_path: Path) -> None:
    client, _ = _make_fake_client(text="")
    adapter = GeminiAdapter(GeminiConfig(), client=client)
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
    )

    assert result.failure_reason == "gemini returned an empty response"
    assert result.response.claimed_success is False


def test_gemini_adapter_schema_violation_sets_failure_reason(tmp_path: Path) -> None:
    # Valid JSON, but missing required fields.
    client, _ = _make_fake_client(text=json.dumps({"foo": "bar"}))
    adapter = GeminiAdapter(GeminiConfig(), client=client)
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
    )

    assert result.failure_reason is not None
    assert "invalid JSON" in result.failure_reason
    assert result.response.claimed_success is False
    assert result.events[-1].kind == "adapter.failed"


def test_gemini_adapter_sdk_exception_returns_failure(tmp_path: Path) -> None:
    client, _ = _make_fake_client(
        text="",
        raise_on_generate=RuntimeError("transport broke"),
    )
    adapter = GeminiAdapter(GeminiConfig(), client=client)
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
    )

    assert result.failure_reason is not None
    assert "transport broke" in result.failure_reason
    assert result.response.claimed_success is False


def test_gemini_adapter_missing_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    adapter = GeminiAdapter(GeminiConfig())  # no client override
    result = adapter.run(
        prompt="please fix",
        workspace=tmp_path,
        attempt=1,
        schema_path=None,
    )

    assert result.failure_reason is not None
    # Could be either missing-key or missing-SDK; both surface as failure_reason.
    assert (
        "GEMINI_API_KEY" in result.failure_reason
        or "google-genai" in result.failure_reason
    )
    assert result.response.claimed_success is False
