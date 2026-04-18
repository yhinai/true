from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

POSITIONAL_ONLY = "positional_only"
POSITIONAL_OR_KEYWORD = "positional_or_keyword"
VAR_POSITIONAL = "var_positional"
KEYWORD_ONLY = "keyword_only"
VAR_KEYWORD = "var_keyword"


@dataclass(frozen=True)
class ContractParameter:
    name: str
    kind: str
    annotation: str | None = None
    has_default: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "annotation": self.annotation,
            "has_default": self.has_default,
        }


@dataclass(frozen=True)
class ContractSignature:
    name: str
    parameters: tuple[ContractParameter, ...]
    return_annotation: str | None = None
    source: str | None = None
    lineno: int | None = None

    @property
    def min_positional_args(self) -> int:
        count = 0
        for parameter in self.parameters:
            if parameter.kind not in (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD):
                continue
            if parameter.has_default:
                continue
            count += 1
        return count

    @property
    def max_positional_args(self) -> int | None:
        if self.accepts_var_positional:
            return None
        count = 0
        for parameter in self.parameters:
            if parameter.kind in (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD):
                count += 1
        return count

    @property
    def accepts_var_positional(self) -> bool:
        return any(parameter.kind == VAR_POSITIONAL for parameter in self.parameters)

    @property
    def accepts_var_keyword(self) -> bool:
        return any(parameter.kind == VAR_KEYWORD for parameter in self.parameters)

    @property
    def required_parameter_names(self) -> tuple[str, ...]:
        names: list[str] = []
        for parameter in self.parameters:
            if parameter.kind in (VAR_POSITIONAL, VAR_KEYWORD):
                continue
            if parameter.has_default:
                continue
            names.append(parameter.name)
        return tuple(names)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "parameters": [parameter.as_dict() for parameter in self.parameters],
            "return_annotation": self.return_annotation,
            "source": self.source,
            "lineno": self.lineno,
            "min_positional_args": self.min_positional_args,
            "max_positional_args": self.max_positional_args,
            "accepts_var_positional": self.accepts_var_positional,
            "accepts_var_keyword": self.accepts_var_keyword,
        }


@dataclass(frozen=True)
class ContractSpec:
    signature: ContractSignature
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    description: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "signature": self.signature.as_dict(),
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "description": self.description,
            "metadata": dict(self.metadata),
        }


def extract_signatures_from_source(
    source_text: str,
    *,
    source_name: str = "<memory>",
    include_private: bool = False,
) -> dict[str, ContractSignature]:
    tree = ast.parse(source_text, filename=source_name)
    signatures: dict[str, ContractSignature] = {}
    for function in _iter_function_nodes(tree):
        if not include_private and function.name.startswith("_"):
            continue
        signatures[function.name] = signature_from_function_def(function, source_name=source_name)
    return signatures


def extract_contracts_from_source(
    source_text: str,
    *,
    source_name: str = "<memory>",
    include_private: bool = False,
) -> dict[str, ContractSpec]:
    tree = ast.parse(source_text, filename=source_name)
    contracts: dict[str, ContractSpec] = {}

    for function in _iter_function_nodes(tree):
        if not include_private and function.name.startswith("_"):
            continue

        signature = signature_from_function_def(function, source_name=source_name)
        preconditions: list[str] = []
        postconditions: list[str] = []

        for decorator in function.decorator_list:
            decorator_name = _decorator_name(decorator)
            decorator_text = ast.get_source_segment(source_text, decorator) or decorator_name
            if decorator_name.endswith("require") or decorator_name.endswith("pre"):
                preconditions.append(decorator_text)
            if decorator_name.endswith("ensure") or decorator_name.endswith("post"):
                postconditions.append(decorator_text)

        docstring = ast.get_docstring(function)
        if docstring:
            for raw_line in docstring.splitlines():
                line = raw_line.strip()
                lowered = line.lower()
                if lowered.startswith("pre:"):
                    preconditions.append(line[4:].strip())
                if lowered.startswith("post:"):
                    postconditions.append(line[5:].strip())

        contracts[function.name] = ContractSpec(
            signature=signature,
            preconditions=tuple(preconditions),
            postconditions=tuple(postconditions),
            description=(docstring.strip().splitlines()[0] if docstring else None),
            metadata={"source_name": source_name},
        )

    return contracts


def load_contracts_from_file(path: str | Path, *, include_private: bool = False) -> dict[str, ContractSpec]:
    source_path = Path(path)
    source_text = source_path.read_text(encoding="utf-8")
    return extract_contracts_from_source(
        source_text,
        source_name=str(source_path),
        include_private=include_private,
    )


def signature_from_function_def(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    source_name: str = "<memory>",
) -> ContractSignature:
    parameters: list[ContractParameter] = []

    positional = [*node.args.posonlyargs, *node.args.args]
    positional_defaults = [False] * len(positional)
    for index in range(1, len(node.args.defaults) + 1):
        positional_defaults[-index] = True

    for parameter, has_default in zip(positional, positional_defaults):
        kind = POSITIONAL_ONLY if parameter in node.args.posonlyargs else POSITIONAL_OR_KEYWORD
        parameters.append(
            ContractParameter(
                name=parameter.arg,
                kind=kind,
                annotation=_annotation_text(parameter.annotation),
                has_default=has_default,
            )
        )

    if node.args.vararg is not None:
        parameters.append(
            ContractParameter(
                name=node.args.vararg.arg,
                kind=VAR_POSITIONAL,
                annotation=_annotation_text(node.args.vararg.annotation),
                has_default=False,
            )
        )

    for parameter, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        parameters.append(
            ContractParameter(
                name=parameter.arg,
                kind=KEYWORD_ONLY,
                annotation=_annotation_text(parameter.annotation),
                has_default=default is not None,
            )
        )

    if node.args.kwarg is not None:
        parameters.append(
            ContractParameter(
                name=node.args.kwarg.arg,
                kind=VAR_KEYWORD,
                annotation=_annotation_text(node.args.kwarg.annotation),
                has_default=False,
            )
        )

    return ContractSignature(
        name=node.name,
        parameters=tuple(parameters),
        return_annotation=_annotation_text(node.returns),
        source=source_name,
        lineno=getattr(node, "lineno", None),
    )


def _annotation_text(annotation: ast.AST | None) -> str | None:
    if annotation is None:
        return None
    if hasattr(ast, "unparse"):
        return ast.unparse(annotation)
    return None


def _decorator_name(decorator: ast.expr) -> str:
    target: ast.expr = decorator
    while isinstance(target, ast.Call):
        target = target.func

    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        parts: list[str] = []
        current: ast.expr | None = target
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return "unknown"


def _iter_function_nodes(tree: ast.AST) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]:
    nodes: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append(node)
    nodes.sort(key=lambda item: getattr(item, "lineno", 0))
    return tuple(nodes)
