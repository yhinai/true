from __future__ import annotations

from cbc.models import ModelEvent


def text_event(kind: str, text: str) -> ModelEvent:
    return ModelEvent(kind=kind, payload={"text": text})
