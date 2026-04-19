"""Loader for stacked program.md instructions (global + per-task)."""

from __future__ import annotations

from pathlib import Path


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").rstrip()


def load_program(task_dir: Path, repo_root: Path) -> str:
    """Return the stacked program text.

    Looks up:
      - <repo_root>/program.md or <repo_root>/.cbc/program.md (global)
      - <task_dir>/program.md (per-task)

    Stacking: global first, then "---" separator, then per-task.
    Per-task wins on conflict by coming second.
    Returns "" if neither file exists.
    """
    global_text = _read(repo_root / "program.md") or _read(repo_root / ".cbc" / "program.md")
    task_text = _read(task_dir / "program.md")

    if global_text and task_text:
        return f"{global_text}\n\n---\n\n{task_text}"
    return global_text or task_text or ""
