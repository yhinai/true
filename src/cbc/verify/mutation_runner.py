from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class MutationCandidate:
    candidate_id: str
    description: str
    line: int
    column: int
    original: str
    replacement: str
    mutated_source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "description": self.description,
            "line": self.line,
            "column": self.column,
            "original": self.original,
            "replacement": self.replacement,
        }


@dataclass(frozen=True)
class MutationRunResult:
    total_candidates: int
    killed: int
    survived: int
    errored: int
    details: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_candidates": self.total_candidates,
            "killed": self.killed,
            "survived": self.survived,
            "errored": self.errored,
            "details": list(self.details),
        }


def generate_simple_mutations(source_text: str, *, max_mutations: int = 25) -> tuple[MutationCandidate, ...]:
    replacements: tuple[tuple[str, str], ...] = (
        ("==", "!="),
        ("!=", "=="),
        (">=", "<"),
        ("<=", ">"),
        (">", "<"),
        ("<", ">"),
        (" + ", " - "),
        (" - ", " + "),
        (" and ", " or "),
        (" or ", " and "),
        ("True", "False"),
        ("False", "True"),
    )

    candidates: list[MutationCandidate] = []
    seen_ranges: set[tuple[int, int]] = set()
    for original, replacement in replacements:
        for match in re.finditer(re.escape(original), source_text):
            start, end = match.span()
            if (start, end) in seen_ranges:
                continue
            seen_ranges.add((start, end))
            mutated_source = source_text[:start] + replacement + source_text[end:]
            line, column = _line_and_column(source_text, start)
            candidate = MutationCandidate(
                candidate_id=f"mut_{len(candidates) + 1}",
                description=f"Replace '{original}' with '{replacement}'",
                line=line,
                column=column,
                original=original,
                replacement=replacement,
                mutated_source=mutated_source,
            )
            candidates.append(candidate)
            if len(candidates) >= max_mutations:
                return tuple(candidates)
    return tuple(candidates)


def run_mutation_campaign(
    source_text: str,
    verifier: Callable[[str], bool],
    *,
    max_mutations: int = 25,
) -> MutationRunResult:
    candidates = generate_simple_mutations(source_text, max_mutations=max_mutations)
    killed = 0
    survived = 0
    errored = 0
    details: list[dict[str, Any]] = []

    for candidate in candidates:
        outcome: str
        error_message: str | None = None
        try:
            verification_passed = verifier(candidate.mutated_source)
            if verification_passed:
                survived += 1
                outcome = "survived"
            else:
                killed += 1
                outcome = "killed"
        except Exception as error:  # noqa: BLE001
            errored += 1
            outcome = "errored"
            error_message = str(error)

        detail = candidate.as_dict()
        detail["outcome"] = outcome
        if error_message:
            detail["error"] = error_message
        details.append(detail)

    return MutationRunResult(
        total_candidates=len(candidates),
        killed=killed,
        survived=survived,
        errored=errored,
        details=tuple(details),
    )


def _line_and_column(text: str, index: int) -> tuple[int, int]:
    prefix = text[:index]
    line = prefix.count("\n") + 1
    if "\n" in prefix:
        column = index - prefix.rfind("\n")
    else:
        column = index + 1
    return line, column
