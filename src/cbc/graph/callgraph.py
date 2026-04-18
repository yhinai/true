from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CallSite:
    caller: str
    callee: str
    lineno: int
    col_offset: int
    arg_count: int
    keyword_names: tuple[str, ...]
    has_starargs: bool
    has_kwargs: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "caller": self.caller,
            "callee": self.callee,
            "lineno": self.lineno,
            "col_offset": self.col_offset,
            "arg_count": self.arg_count,
            "keyword_names": list(self.keyword_names),
            "has_starargs": self.has_starargs,
            "has_kwargs": self.has_kwargs,
        }


@dataclass(frozen=True)
class CallGraph:
    module_name: str
    nodes: tuple[str, ...]
    edges: tuple[CallSite, ...]

    def outgoing(self, function_name: str) -> tuple[CallSite, ...]:
        return tuple(edge for edge in self.edges if edge.caller == function_name)

    def incoming(self, function_name: str) -> tuple[CallSite, ...]:
        return tuple(edge for edge in self.edges if edge.callee == function_name)

    def as_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "nodes": list(self.nodes),
            "edges": [edge.as_dict() for edge in self.edges],
        }


def extract_call_graph_from_source(
    source_text: str,
    *,
    module_name: str = "<memory>",
    include_external_calls: bool = False,
) -> CallGraph:
    tree = ast.parse(source_text, filename=module_name)
    visitor = _CallGraphVisitor()
    visitor.visit(tree)

    nodes = tuple(sorted(visitor.function_names))
    if include_external_calls:
        edges = tuple(sorted(visitor.calls, key=lambda edge: (edge.caller, edge.lineno, edge.col_offset)))
    else:
        edges = tuple(
            sorted(
                (edge for edge in visitor.calls if edge.callee in visitor.function_names),
                key=lambda edge: (edge.caller, edge.lineno, edge.col_offset),
            )
        )

    return CallGraph(module_name=module_name, nodes=nodes, edges=edges)


def extract_call_graph_from_file(path: str | Path, *, include_external_calls: bool = False) -> CallGraph:
    source_path = Path(path)
    source_text = source_path.read_text(encoding="utf-8")
    return extract_call_graph_from_source(
        source_text,
        module_name=str(source_path),
        include_external_calls=include_external_calls,
    )


class _CallGraphVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_names: set[str] = set()
        self.calls: list[CallSite] = []
        self._function_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_names.add(node.name)
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_names.add(node.name)
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._function_stack:
            callee = _resolve_callee_name(node.func)
            if callee:
                keyword_names: list[str] = []
                has_kwargs = False
                for keyword in node.keywords:
                    if keyword.arg is None:
                        has_kwargs = True
                    else:
                        keyword_names.append(keyword.arg)

                call_site = CallSite(
                    caller=self._function_stack[-1],
                    callee=callee,
                    lineno=getattr(node, "lineno", 0),
                    col_offset=getattr(node, "col_offset", 0),
                    arg_count=len(node.args),
                    keyword_names=tuple(keyword_names),
                    has_starargs=any(isinstance(argument, ast.Starred) for argument in node.args),
                    has_kwargs=has_kwargs,
                )
                self.calls.append(call_site)
        self.generic_visit(node)


def _resolve_callee_name(function_expr: ast.expr) -> str | None:
    if isinstance(function_expr, ast.Name):
        return function_expr.id
    if isinstance(function_expr, ast.Attribute):
        return function_expr.attr
    return None
