from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AxiomName(str, Enum):
    TOTALITY = "Totality"
    NON_CONTRADICTION = "Non-Contradiction"
    IDENTITY = "Identity"
    REFERENTIAL_INTEGRITY = "Referential Integrity"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    UNPROVEN = "UNPROVEN"


class BugClassification(BaseModel):
    axiom: AxiomName
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    target_function: str
    bug_summary: str


class PatchProposal(BaseModel):
    function_name: str
    patched_source: str
    diff_summary: str
    changed_lines: int = Field(ge=0)
    rationale: str


class ContractProposal(BaseModel):
    function_name: str
    decorators: list[str]
    contract_block: str
    rationale: str


class VerificationOutcome(BaseModel):
    status: VerificationStatus
    raw_output: str
    command: list[str]
    counterexample: str | None = None
    violated_condition: str | None = None
    timeout_seconds: float | None = None
    explored_paths: int | None = None


class TestRunResult(BaseModel):
    __test__ = False
    command: list[str]
    passed: int = 0
    failed: int = 0
    ok: bool
    output: str


class EvidenceLedgerModel(BaseModel):
    bug_summary: str
    axiom: AxiomName
    function_name: str
    patch_summary: str
    patched_source: str
    contracts: list[str]
    verification: VerificationOutcome
    tests: TestRunResult | None = None
    wall_time_seconds: float = Field(ge=0.0)
    final_status: VerificationStatus
