from __future__ import annotations

import re

from .axioms import (
    build_identity_contracts,
    build_non_contradiction_contracts,
    build_referential_integrity_contracts,
    build_totality_contracts,
)
from .schema import AxiomName, BugClassification, ContractProposal


class ContractGenerator:
    def derive(self, classification: BugClassification, function_source: str) -> ContractProposal:
        function_name = classification.target_function
        if classification.axiom == AxiomName.TOTALITY:
            decorators = build_totality_contracts(function_name, function_source)
        elif classification.axiom == AxiomName.NON_CONTRADICTION:
            decorators = build_non_contradiction_contracts(function_name, function_source)
        elif classification.axiom == AxiomName.IDENTITY:
            decorators = build_identity_contracts(function_name, function_source)
        else:
            decorators = build_referential_integrity_contracts(function_name, function_source)

        return ContractProposal(
            function_name=function_name,
            decorators=decorators,
            contract_block="\n".join(decorators),
            rationale=f"Derived simple {classification.axiom.value} contracts that CrossHair can check quickly.",
        )

    def apply_contracts(self, patched_source: str, function_name: str, decorators: list[str]) -> str:
        lines = patched_source.splitlines()
        prelude: list[str] = ["import math", "import icontract"]
        existing_imports = [line for line in lines if line.strip().startswith(("import ", "from "))]
        merged_imports = prelude + [line for line in existing_imports if line not in prelude]
        body = [line for line in lines if line not in existing_imports]

        target_index = self._find_function_line_index(body, function_name)
        if target_index is None:
            target_index = self._find_first_function_line_index(body)
        if target_index is None:
            target_index = 0

        updated_body = body[:target_index] + decorators + body[target_index:]
        normalized_body = self._strip_leading_blank_lines(updated_body)
        return "\n".join(merged_imports + [""] + normalized_body) + "\n"

    @staticmethod
    def _find_function_line_index(lines: list[str], function_name: str) -> int | None:
        pattern = re.compile(rf"^\s*(?:async\s+def|def)\s+{re.escape(function_name)}\s*\(")
        for index, line in enumerate(lines):
            if pattern.search(line):
                return index
        return None

    @staticmethod
    def _find_first_function_line_index(lines: list[str]) -> int | None:
        pattern = re.compile(r"^\s*(?:async\s+def|def)\s+\w+\s*\(")
        for index, line in enumerate(lines):
            if pattern.search(line):
                return index
        return None

    @staticmethod
    def _strip_leading_blank_lines(lines: list[str]) -> list[str]:
        while lines and not lines[0].strip():
            lines = lines[1:]
        return lines
