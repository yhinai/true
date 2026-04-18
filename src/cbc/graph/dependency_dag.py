from __future__ import annotations

import ast
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable

from cbc.graph.callgraph import CallGraph


@dataclass(frozen=True)
class DependencyDAG:
    module_name: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def outgoing(self, node: str) -> tuple[str, ...]:
        return tuple(target for source, target in self.edges if source == node)

    def incoming(self, node: str) -> tuple[str, ...]:
        return tuple(source for source, target in self.edges if target == node)

    def as_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "nodes": list(self.nodes),
            "edges": [list(edge) for edge in self.edges],
        }


def extract_import_dependency_dag_from_source(
    source_text: str,
    *,
    module_name: str = "<memory>",
) -> DependencyDAG:
    tree = ast.parse(source_text, filename=module_name)
    nodes: set[str] = {module_name}
    edges: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported = alias.name
                nodes.add(imported)
                edges.add((module_name, imported))
        if isinstance(node, ast.ImportFrom):
            prefix = "." * node.level if node.level else ""
            base = f"{prefix}{node.module}" if node.module else prefix or "<relative>"
            nodes.add(base)
            edges.add((module_name, base))

    return DependencyDAG(
        module_name=module_name,
        nodes=tuple(sorted(nodes)),
        edges=tuple(sorted(edges)),
    )


def build_function_dependency_dag(call_graph: CallGraph) -> DependencyDAG:
    edges = {(edge.caller, edge.callee) for edge in call_graph.edges}
    nodes: set[str] = set(call_graph.nodes)
    for source, target in edges:
        nodes.add(source)
        nodes.add(target)

    return DependencyDAG(
        module_name=call_graph.module_name,
        nodes=tuple(sorted(nodes)),
        edges=tuple(sorted(edges)),
    )


def bounded_dependency_edges(
    dag: DependencyDAG,
    *,
    roots: Iterable[str],
    max_depth: int = 2,
    max_nodes: int = 50,
) -> tuple[tuple[str, str], ...]:
    if max_depth < 0 or max_nodes <= 0:
        return ()

    queue: deque[tuple[str, int]] = deque((root, 0) for root in roots)
    seen: set[str] = set()
    kept_edges: set[tuple[str, str]] = set()

    adjacency: dict[str, list[str]] = {}
    for source, target in dag.edges:
        adjacency.setdefault(source, []).append(target)

    while queue and len(seen) < max_nodes:
        node, depth = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if depth >= max_depth:
            continue
        for target in adjacency.get(node, []):
            kept_edges.add((node, target))
            if target not in seen:
                queue.append((target, depth + 1))

    return tuple(sorted(kept_edges))
