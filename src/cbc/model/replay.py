from __future__ import annotations

import json
from pathlib import Path

from cbc.model.adapter import ModelAdapter
from cbc.model.events import text_event
from cbc.models import ModelEvent, ModelResponse


class ReplayModelAdapter(ModelAdapter):
    name = "replay"

    def __init__(self, replay_file: Path) -> None:
        self._payload = json.loads(replay_file.read_text(encoding="utf-8"))
        if isinstance(self._payload, list):
            self._responses = [ModelResponse.model_validate(item) for item in self._payload]
        else:
            self._responses = []

    def run(
        self,
        *,
        prompt: str,
        workspace: Path,
        attempt: int,
        candidate_index: int = 0,
        candidate_role: str = "primary",
        schema_path: Path | None = None,
    ) -> tuple[ModelResponse, list[ModelEvent]]:
        response = self._resolve_response(attempt=attempt, candidate_index=candidate_index)
        events = [text_event("replay_prompt", prompt), text_event("replay_summary", response.summary)]
        return response, events

    def _resolve_response(self, *, attempt: int, candidate_index: int) -> ModelResponse:
        if self._responses:
            index = min(attempt - 1, len(self._responses) - 1)
            return self._responses[index]

        attempts = self._payload.get("attempts", [])
        if not isinstance(attempts, list) or not attempts:
            raise ValueError("Replay payload must be a list of responses or an object with a non-empty 'attempts' list.")
        selected_attempt = attempts[min(attempt - 1, len(attempts) - 1)]
        if isinstance(selected_attempt, list):
            candidates = selected_attempt
        elif isinstance(selected_attempt, dict) and isinstance(selected_attempt.get("candidates"), list):
            candidates = selected_attempt["candidates"]
        elif isinstance(selected_attempt, dict):
            return ModelResponse.model_validate(selected_attempt.get("response", selected_attempt))
        else:
            raise ValueError("Replay attempt entries must be objects or candidate lists.")
        if not candidates:
            raise ValueError("Replay candidate list must not be empty.")
        index = min(candidate_index, len(candidates) - 1)
        return ModelResponse.model_validate(candidates[index])
