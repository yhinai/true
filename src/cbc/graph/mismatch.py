from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from cbc.graph.callgraph import CallSite, extract_call_graph_from_source
from cbc.graph.slicer import bounded_call_slice
from cbc.verify.contract_ir import (
    KEYWORD_ONLY,
    POSITIONAL_ONLY,
    POSITIONAL_OR_KEYWORD,
    VAR_KEYWORD,
    VAR_POSITIONAL,
    ContractSignature,
    extract_signatures_from_source,
)


@dataclass(frozen=True)
class SignatureMismatch:
    caller: str
    callee: str
    lineno: int
    col_offset: int
    kind: str
    message: str
    observed: dict[str, Any]
    expected: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "caller": self.caller,
            "callee": self.callee,
            "lineno": self.lineno,
            "col_offset": self.col_offset,
            "kind": self.kind,
            "message": self.message,
            "observed": self.observed,
            "expected": self.expected,
        }


def detect_bounded_signature_mismatches(
    source_text: str,
    *,
    module_name: str = "<memory>",
    roots: Iterable[str] | None = None,
    max_depth: int = 2,
    max_nodes: int = 50,
    include_private: bool = False,
) -> tuple[SignatureMismatch, ...]:
    signatures = extract_signatures_from_source(
        source_text,
        source_name=module_name,
        include_private=include_private,
    )
    call_graph = extract_call_graph_from_source(
        source_text,
        module_name=module_name,
        include_external_calls=True,
    )
    if roots is not None:
        call_graph = bounded_call_slice(
            call_graph,
            roots=roots,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )

    mismatches: list[SignatureMismatch] = []
    for edge in call_graph.edges:
        signature = signatures.get(edge.callee)
        if signature is None:
            continue
        mismatch = _mismatch_for_call(edge=edge, signature=signature)
        if mismatch is not None:
            mismatches.append(mismatch)
    return tuple(mismatches)


def detect_bounded_signature_mismatches_in_file(
    path: str | Path,
    *,
    roots: Iterable[str] | None = None,
    max_depth: int = 2,
    max_nodes: int = 50,
    include_private: bool = False,
) -> tuple[SignatureMismatch, ...]:
    source_path = Path(path)
    source_text = source_path.read_text(encoding="utf-8")
    return detect_bounded_signature_mismatches(
        source_text,
        module_name=str(source_path),
        roots=roots,
        max_depth=max_depth,
        max_nodes=max_nodes,
        include_private=include_private,
    )


def format_mismatches(mismatches: Iterable[SignatureMismatch]) -> str:
    lines: list[str] = []
    for mismatch in mismatches:
        lines.append(
            f"{mismatch.caller} -> {mismatch.callee}:{mismatch.lineno}:{mismatch.col_offset} "
            f"[{mismatch.kind}] {mismatch.message}"
        )
    return "\n".join(lines)


def _mismatch_for_call(edge: CallSite, signature: ContractSignature) -> SignatureMismatch | None:
    if edge.has_starargs or edge.has_kwargs:
        return None

    parameters = signature.parameters
    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind in (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD)
    ]

    if signature.max_positional_args is not None and edge.arg_count > signature.max_positional_args:
        return SignatureMismatch(
            caller=edge.caller,
            callee=edge.callee,
            lineno=edge.lineno,
            col_offset=edge.col_offset,
            kind="too_many_positional",
            message=(
                f"{edge.callee} accepts at most {signature.max_positional_args} positional arguments "
                f"but call provides {edge.arg_count}."
            ),
            observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
            expected={
                "min_positional_args": signature.min_positional_args,
                "max_positional_args": signature.max_positional_args,
            },
        )

    bound_names: set[str] = set()
    for index in range(min(edge.arg_count, len(positional_parameters))):
        bound_names.add(positional_parameters[index].name)

    parameter_by_name = {parameter.name: parameter for parameter in parameters}
    for keyword_name in edge.keyword_names:
        parameter = parameter_by_name.get(keyword_name)
        if keyword_name in bound_names:
            return SignatureMismatch(
                caller=edge.caller,
                callee=edge.callee,
                lineno=edge.lineno,
                col_offset=edge.col_offset,
                kind="duplicate_argument",
                message=f"{keyword_name} is provided both positionally and by keyword.",
                observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
                expected={"signature": signature.as_dict()},
            )
        if parameter is None:
            if not signature.accepts_var_keyword:
                return SignatureMismatch(
                    caller=edge.caller,
                    callee=edge.callee,
                    lineno=edge.lineno,
                    col_offset=edge.col_offset,
                    kind="unknown_keyword",
                    message=f"{edge.callee} has no parameter named '{keyword_name}'.",
                    observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
                    expected={"signature": signature.as_dict()},
                )
            continue
        if parameter.kind == POSITIONAL_ONLY:
            return SignatureMismatch(
                caller=edge.caller,
                callee=edge.callee,
                lineno=edge.lineno,
                col_offset=edge.col_offset,
                kind="positional_only_by_keyword",
                message=f"{keyword_name} is positional-only in {edge.callee}.",
                observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
                expected={"signature": signature.as_dict()},
            )
        if parameter.kind == VAR_POSITIONAL:
            return SignatureMismatch(
                caller=edge.caller,
                callee=edge.callee,
                lineno=edge.lineno,
                col_offset=edge.col_offset,
                kind="var_positional_by_keyword",
                message=f"{keyword_name} refers to *args which cannot be passed by keyword.",
                observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
                expected={"signature": signature.as_dict()},
            )
        bound_names.add(keyword_name)

    required: list[str] = []
    for parameter in parameters:
        if parameter.kind in (VAR_POSITIONAL, VAR_KEYWORD):
            continue
        if parameter.has_default:
            continue
        required.append(parameter.name)

    missing = sorted(name for name in required if name not in bound_names)
    if missing:
        return SignatureMismatch(
            caller=edge.caller,
            callee=edge.callee,
            lineno=edge.lineno,
            col_offset=edge.col_offset,
            kind="missing_required",
            message=f"Missing required argument(s): {', '.join(missing)}.",
            observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
            expected={"required": required, "signature": signature.as_dict()},
        )

    required_keyword_only = [
        parameter.name
        for parameter in parameters
        if parameter.kind == KEYWORD_ONLY and not parameter.has_default
    ]
    missing_keyword_only = [name for name in required_keyword_only if name not in bound_names]
    if missing_keyword_only:
        return SignatureMismatch(
            caller=edge.caller,
            callee=edge.callee,
            lineno=edge.lineno,
            col_offset=edge.col_offset,
            kind="missing_keyword_only",
            message=f"Missing required keyword-only argument(s): {', '.join(missing_keyword_only)}.",
            observed={"positional_args": edge.arg_count, "keywords": list(edge.keyword_names)},
            expected={"required_keyword_only": required_keyword_only, "signature": signature.as_dict()},
        )

    return None
