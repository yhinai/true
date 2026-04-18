from __future__ import annotations

import json
from pathlib import Path

from cbc.model.adapter import ModelAdapter
from cbc.model.events import text_event
from cbc.models import ModelEvent, ModelResponse


class ReplayModelAdapter(ModelAdapter):
    name = "replay"

    def __init__(self, replay_file: Path) -> None:
        self._responses = [
            ModelResponse.model_validate(item)
            for item in json.loads(replay_file.read_text(encoding="utf-8"))
        ]

    def run(
        self,
        *,
        prompt: str,
        workspace: Path,
        attempt: int,
        schema_path: Path | None = None,
    ) -> tuple[ModelResponse, list[ModelEvent]]:
        index = min(attempt - 1, len(self._responses) - 1)
        response = self._responses[index]
        events = [text_event("replay_prompt", prompt), text_event("replay_summary", response.summary)]
        return response, events
