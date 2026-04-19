"""Environment sanitization helpers for verify subprocesses.

These helpers scrub credentials and similar secrets out of the environment
passed to task-controlled subprocesses spawned by the verify layer.
"""
from __future__ import annotations

from typing import Mapping

# Credentials prefixes that must never leak to task-controlled child processes.
SENSITIVE_PREFIXES: tuple[str, ...] = (
    "SUPABASE_",
    "VERCEL_",
    "OPENAI_",
    "GEMINI_",
    "GOOGLE_",
    "ANTHROPIC_",
    "GITHUB_TOKEN",
    "POSTGRES_",
    "AWS_",
)

# Bare environment keys that must be dropped even without a matching prefix.
SENSITIVE_KEYS: frozenset[str] = frozenset({"PGPASSWORD", "DATABASE_URL"})

# Keys that must always be preserved (baseline runtime requirements).
# LC_* is handled as a prefix check alongside this set.
PRESERVED_KEYS: frozenset[str] = frozenset({"PATH", "HOME", "TMPDIR", "LANG"})


def _is_preserved(key: str) -> bool:
    return key in PRESERVED_KEYS or key.startswith("LC_")


def _is_sensitive(key: str) -> bool:
    if key in SENSITIVE_KEYS:
        return True
    return any(key.startswith(prefix) for prefix in SENSITIVE_PREFIXES)


def scrub_env(base_env: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of ``base_env`` with sensitive keys removed.

    Preserved keys (``PATH``/``HOME``/``TMPDIR``/``LANG``/``LC_*``) are kept
    even if they somehow collide with a sensitive prefix, to guarantee the
    child process retains a working runtime baseline.
    """
    scrubbed: dict[str, str] = {}
    for key, value in base_env.items():
        if _is_preserved(key):
            scrubbed[key] = value
            continue
        if _is_sensitive(key):
            continue
        scrubbed[key] = value
    return scrubbed
