from __future__ import annotations

from collections import deque
from typing import Iterable

from cbc.graph.callgraph import CallGraph, CallSite
from cbc.graph.dependency_dag import DependencyDAG, bounded_dependency_edges


def bounded_call_slice(
    call_graph: CallGraph,
    roots: Iterable[str],
    *,
    max_depth: int = 2,
    max_nodes: int = 50,
) -> CallGraph:
    if max_depth < 0 or max_nodes <= 0:
        return CallGraph(module_name=call_graph.module_name, nodes=(), edges=())

    queue: deque[tuple[str, int]] = deque((root, 0) for root in roots)
    seen: set[str] = set()
    edges: list[CallSite] = []

    adjacency: dict[str, list[CallSite]] = {}
    for edge in call_graph.edges:
        adjacency.setdefault(edge.caller, []).append(edge)

    while queue and len(seen) < max_nodes:
        node, depth = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if depth >= max_depth:
            continue
        for edge in adjacency.get(node, []):
            edges.append(edge)
            if edge.callee not in seen:
                queue.append((edge.callee, depth + 1))

    return CallGraph(
        module_name=call_graph.module_name,
        nodes=tuple(sorted(seen)),
        edges=tuple(sorted(edges, key=lambda item: (item.caller, item.lineno, item.col_offset))),
    )


def bounded_dependency_slice(
    dag: DependencyDAG,
    roots: Iterable[str],
    *,
    max_depth: int = 2,
    max_nodes: int = 50,
) -> DependencyDAG:
    kept_edges = bounded_dependency_edges(
        dag,
        roots=roots,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    nodes: set[str] = set(roots)
    for source, target in kept_edges:
        nodes.add(source)
        nodes.add(target)
    return DependencyDAG(
        module_name=dag.module_name,
        nodes=tuple(sorted(nodes)),
        edges=kept_edges,
    )
