import re


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    chunks = [chunk for chunk in re.split(r"[^a-z0-9]+", lowered) if chunk]
    return "-".join(chunks)
