from __future__ import annotations

import ast
from pathlib import Path


def build_dependency_dag(workspace: Path) -> dict[str, list[str]]:
    dag: dict[str, list[str]] = {}
    for path in workspace.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = path.relative_to(workspace).as_posix()
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        dag[module] = sorted(set(imports))
    return dag
