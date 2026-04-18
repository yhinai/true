from __future__ import annotations

import ast
from dataclasses import dataclass


def find_scope_mismatches(changed_files: list[str], allowed_files: list[str]) -> list[str]:
    allowed = set(allowed_files)
    return [path for path in changed_files if allowed and path not in allowed]


@dataclass(frozen=True)
class SignatureMismatch:
    caller: str
    callee: str
    kind: str
    observed_args: int
    expected_args: int


def detect_bounded_signature_mismatches(
    source_text: str,
    *,
    roots: list[str],
    max_depth: int,
) -> tuple[SignatureMismatch, ...]:
    tree = ast.parse(source_text)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    mismatches: list[SignatureMismatch] = []

    def walk(function_name: str, depth: int) -> None:
        if depth > max_depth:
            return
        function = functions.get(function_name)
        if function is None:
            return
        for node in ast.walk(function):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            callee_name = node.func.id
            callee = functions.get(callee_name)
            if callee is not None:
                observed = len(node.args)
                expected = len(callee.args.args)
                if observed > expected:
                    mismatches.append(
                        SignatureMismatch(
                            caller=function_name,
                            callee=callee_name,
                            kind="too_many_positional",
                            observed_args=observed,
                            expected_args=expected,
                        )
                    )
                walk(callee_name, depth + 1)

    for root in roots:
        walk(root, 0)

    return tuple(mismatches)
