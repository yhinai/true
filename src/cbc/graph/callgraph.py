from __future__ import annotations

import ast
from pathlib import Path


def build_callgraph(workspace: Path) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for path in workspace.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = path.relative_to(workspace).as_posix()
        calls: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.append(node.func.id)
        graph[module] = sorted(set(calls))
    return graph
