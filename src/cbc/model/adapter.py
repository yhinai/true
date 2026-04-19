from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from cbc.models import ModelEvent, ModelResponse


class ModelAdapter(ABC):
    name: str

    @abstractmethod
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
        raise NotImplementedError
