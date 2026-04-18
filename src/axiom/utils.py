from __future__ import annotations

import re
from pathlib import Path


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def infer_function_name(source: str, hint_text: str = "") -> str:
    function_names = _extract_function_names(source)
    if not function_names:
        return "unknown_function"

    if hint_text:
        lowered_hint = hint_text.lower()
        for function_name in function_names:
            if re.search(rf"\b{re.escape(function_name.lower())}\b", lowered_hint):
                return function_name

    return function_names[0]


def _extract_function_names(source: str) -> list[str]:
    function_names: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("def ") and "(" in stripped:
            function_names.append(stripped.split("def ", 1)[1].split("(", 1)[0])
    return function_names


def normalize_text_block(text: str) -> str:
    return text.strip() + ("\n" if text.strip() else "")
