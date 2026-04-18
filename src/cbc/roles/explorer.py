from __future__ import annotations

from pathlib import Path

from cbc.models import ExplorerArtifact, TaskSpec

def list_python_files(workspace: Path) -> list[str]:
    return sorted(
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def build_explorer_artifact(task: TaskSpec, workspace: Path) -> ExplorerArtifact:
    python_files = list_python_files(workspace)
    likely_targets = [
        path
        for path in task.allowed_files
        if path.endswith(".py") and path in python_files
    ]
    target_modules = {Path(path).stem for path in likely_targets}

    nearby_tests: list[str] = []
    related_files: list[str] = []
    for path in python_files:
        if path in likely_targets:
            continue
        content = (workspace / path).read_text(encoding="utf-8")
        if target_modules and any(
            marker in content
            for module in target_modules
            for marker in (f"import {module}", f"from {module} import")
        ):
            related_files.append(path)
        if _is_test_file(path) and (
            any(module in Path(path).stem for module in target_modules) or path in related_files
        ):
            nearby_tests.append(path)

    if not likely_targets and python_files:
        likely_targets = python_files[: min(3, len(python_files))]

    if not nearby_tests:
        nearby_tests = [path for path in python_files if _is_test_file(path)][:3]

    notes = [f"python_files_scanned={len(python_files)}"]
    if task.allowed_files:
        notes.append(f"allowed_scope={', '.join(task.allowed_files)}")

    summary = (
        f"Explorer found {len(likely_targets)} likely target file(s), "
        f"{len(nearby_tests)} nearby test file(s), and {len(related_files)} related file(s)."
    )
    return ExplorerArtifact(
        summary=summary,
        likely_targets=likely_targets,
        nearby_tests=nearby_tests,
        related_files=related_files,
        notes=notes,
    )


def _is_test_file(path: str) -> bool:
    name = Path(path).name
    return name.startswith("test_") or name.endswith("_test.py")
