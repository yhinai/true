from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from cbc.config import GeminiConfig
from cbc.model.adapter import ModelAdapter
from cbc.model.events import text_event
from cbc.model.prompts import JSON_RESPONSE_CONTRACT
from cbc.models import AdapterRunResult, ModelEvent, ModelResponse, ModelUsage

logger = logging.getLogger(__name__)


class GeminiAdapter(ModelAdapter):
    """Google Gemini adapter using the unified `google-genai` SDK."""

    name = "gemini"

    def __init__(
        self,
        config: GeminiConfig,
        *,
        task_id: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config
        self.task_id = task_id
        self._client = client  # optional override for tests

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from google import genai  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "google-genai SDK not installed. Install the `gemini` extra: "
                "`uv sync --extra gemini`."
            ) from exc
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Environment variable {self.config.api_key_env} is not set; "
                "Gemini adapter requires an API key."
            )
        return genai.Client(api_key=api_key)

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
        events: list[ModelEvent] = []
        events.append(text_event("adapter.prompt", prompt))
        full_prompt = _augment_prompt_with_schema(prompt, schema_path)

        try:
            client = self._get_client()
        except RuntimeError as exc:
            failure_reason = str(exc)
            events.append(text_event("adapter.failed", failure_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=failure_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[failure_reason],
                ),
                events=events,
                usage=ModelUsage(),
                failure_reason=failure_reason,
            )

        try:
            from google.genai import types  # type: ignore[import-not-found]

            gen_config_kwargs: dict[str, Any] = {
                "response_mime_type": "application/json",
                "temperature": self.config.temperature,
            }
            if self.config.max_output_tokens is not None:
                gen_config_kwargs["max_output_tokens"] = self.config.max_output_tokens
            gen_config = types.GenerateContentConfig(**gen_config_kwargs)

            response = client.models.generate_content(
                model=self.config.default_model,
                contents=full_prompt,
                config=gen_config,
            )
        except Exception as exc:  # noqa: BLE001 - surface every SDK failure uniformly
            failure_reason = f"gemini generate_content failed: {exc}"
            events.append(text_event("adapter.failed", failure_reason))
            return AdapterRunResult(
                response=ModelResponse(
                    summary=failure_reason,
                    claimed_success=False,
                    writes=[],
                    notes=[failure_reason],
                ),
                events=events,
                usage=ModelUsage(),
                failure_reason=failure_reason,
            )

        raw_text = getattr(response, "text", None) or ""
        events.append(text_event("adapter.raw_response", raw_text))
        usage = _extract_usage(response, config=self.config)
        events.append(
            ModelEvent(
                kind="adapter.usage",
                payload={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
            )
        )

        if not raw_text.strip():
            failure_reason = "gemini returned an empty response"
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
            model_response = ModelResponse.model_validate_json(raw_text)
        except ValidationError as exc:
            failure_reason = f"gemini produced invalid JSON output: {exc}"
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
        except json.JSONDecodeError as exc:
            failure_reason = f"gemini produced non-JSON output: {exc}"
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

        return AdapterRunResult(
            response=model_response,
            events=events,
            usage=usage,
            failure_reason=None,
        )


def _augment_prompt_with_schema(prompt: str, schema_path: Path | None) -> str:
    schema_json: str
    if schema_path is not None and schema_path.exists():
        schema_json = schema_path.read_text(encoding="utf-8")
    else:
        schema_json = json.dumps(JSON_RESPONSE_CONTRACT, indent=2)
    return (
        f"{prompt}\n\n"
        "Respond with a single JSON object matching this schema exactly. "
        "Do not include prose, markdown, or code fences.\n\n"
        f"{schema_json}"
    )


def _extract_usage(response: Any, *, config: GeminiConfig) -> ModelUsage:
    metadata = getattr(response, "usage_metadata", None)
    prompt_tokens = _get_int_attr(metadata, "prompt_token_count")
    completion_tokens = _get_int_attr(metadata, "candidates_token_count")
    total_tokens = _get_int_attr(metadata, "total_token_count")
    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens
    estimated_cost_usd: float | None = None
    if (
        config.prompt_token_cost_per_1k is not None
        and config.completion_token_cost_per_1k is not None
    ):
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


def _get_int_attr(obj: Any, attr: str) -> int:
    if obj is None:
        return 0
    value = getattr(obj, attr, None)
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return 0
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0
