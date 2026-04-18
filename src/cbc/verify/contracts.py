from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cbc.graph.callgraph import extract_call_graph_from_source
from cbc.verify.contract_ir import ContractSpec, extract_contracts_from_source


@dataclass(frozen=True)
class ContractEdge:
    caller: str
    callee: str
    lineno: int
    col_offset: int
    arg_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "caller": self.caller,
            "callee": self.callee,
            "lineno": self.lineno,
            "col_offset": self.col_offset,
            "arg_count": self.arg_count,
        }


@dataclass(frozen=True)
class ContractGraph:
    source_name: str
    specs: dict[str, ContractSpec]
    edges: tuple[ContractEdge, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "specs": {name: spec.as_dict() for name, spec in self.specs.items()},
            "edges": [edge.as_dict() for edge in self.edges],
        }


def build_contract_graph_from_source(
    source_text: str,
    *,
    source_name: str = "<memory>",
    include_private: bool = False,
) -> ContractGraph:
    specs = extract_contracts_from_source(
        source_text,
        source_name=source_name,
        include_private=include_private,
    )

    call_graph = extract_call_graph_from_source(
        source_text,
        module_name=source_name,
        include_external_calls=True,
    )

    edges: list[ContractEdge] = []
    for edge in call_graph.edges:
        if edge.caller not in specs:
            continue
        if edge.callee not in specs:
            continue
        edges.append(
            ContractEdge(
                caller=edge.caller,
                callee=edge.callee,
                lineno=edge.lineno,
                col_offset=edge.col_offset,
                arg_count=edge.arg_count,
            )
        )

    return ContractGraph(
        source_name=source_name,
        specs=specs,
        edges=tuple(edges),
    )


def build_contract_graph_from_file(path: str | Path, *, include_private: bool = False) -> ContractGraph:
    source_path = Path(path)
    source_text = source_path.read_text(encoding="utf-8")
    return build_contract_graph_from_source(
        source_text,
        source_name=str(source_path),
        include_private=include_private,
    )


def build_prose_spec_summary(contract_graph: ContractGraph) -> str:
    lines: list[str] = []
    for function_name in sorted(contract_graph.specs):
        spec = contract_graph.specs[function_name]
        signature = spec.signature
        parameter_names = ", ".join(parameter.name for parameter in signature.parameters)
        lines.append(f"{function_name}({parameter_names})")
        if spec.preconditions:
            lines.append(f"  pre: {', '.join(spec.preconditions)}")
        if spec.postconditions:
            lines.append(f"  post: {', '.join(spec.postconditions)}")
        if spec.description:
            lines.append(f"  about: {spec.description}")
    return "\n".join(lines)
