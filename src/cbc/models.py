from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from cbc.config import SandboxMode
from cbc.headless_contract import (
    BENCHMARK_COMPARISON_KIND,
    CONTROLLER_COMPARISON_KIND,
    contract_metadata,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class VerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    UNPROVEN = "UNPROVEN"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FileWrite(BaseModel):
    path: str
    content: str
    executable: bool = False


class ModelResponse(BaseModel):
    summary: str
    claimed_success: bool = True
    writes: list[FileWrite] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ModelEvent(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ModelUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None


class AdapterRunResult(BaseModel):
    response: ModelResponse
    events: list[ModelEvent] = Field(default_factory=list)
    usage: ModelUsage = Field(default_factory=ModelUsage)
    failure_reason: str | None = None

    def __iter__(self):
        yield self.response
        yield self.events


class OracleSpec(BaseModel):
    name: str
    kind: Literal["shell", "pytest", "python"] = "shell"
    command: str
    success_exit_codes: list[int] = Field(default_factory=lambda: [0])


class VerificationOptions(BaseModel):
    lint_command: str = "python3 -m compileall ."
    typecheck_enabled: bool = False
    typecheck_command: str | None = None
    coverage_enabled: bool = False
    coverage_command: str | None = None
    crosshair_enabled: bool = False
    crosshair_command: str | None = None
    mutation_enabled: bool = False
    mutation_command: str | None = None


class HypothesisCheckSpec(BaseModel):
    path: str
    function: str
    cases: list[Any] = Field(default_factory=list)
    generated_case_strategy: Literal["string_edge_cases", "small_integers"] | None = None
    generated_case_limit: int = 0
    artifact_name: str = "counterexample.json"
    regression_test_path: str | None = None


class CodexTaskConfig(BaseModel):
    model: str | None = None
    sandbox: SandboxMode | None = None
    profile: str | None = None
    config_overrides: list[str] = Field(default_factory=list)
    add_dirs: list[Path] = Field(default_factory=list)
    skip_git_repo_check: bool | None = None
    dangerously_bypass_approvals: bool | None = None


class TaskSpec(BaseModel):
    task_id: str
    title: str
    prompt: str
    workspace: Path
    allowed_files: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)
    doubt_points: list[str] = Field(default_factory=list)
    oracles: list[OracleSpec]
    adapter: Literal["codex", "replay"] = "replay"
    replay_file: Path | None = None
    retry_budget: int = 2
    timeout_seconds: int = 120
    tags: list[str] = Field(default_factory=list)
    review_checks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    verification: VerificationOptions = Field(default_factory=VerificationOptions)
    hypothesis: HypothesisCheckSpec | None = None
    codex: CodexTaskConfig = Field(default_factory=CodexTaskConfig)

    @model_validator(mode="after")
    def validate_replay_file(self) -> "TaskSpec":
        if self.adapter == "replay" and not self.replay_file:
            raise ValueError("replay_file is required when adapter='replay'")
        return self


class PlanArtifact(BaseModel):
    summary: str
    allowed_files: list[str]
    required_checks: list[str]
    doubt_points: list[str]


class ExplorerArtifact(BaseModel):
    summary: str
    likely_targets: list[str] = Field(default_factory=list)
    nearby_tests: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    passed_checks: int = 0
    unsafe_claim: bool = False
    changed_files: int = 0
    diff_additions: int = 0
    diff_deletions: int = 0
    weighted_score: float = 0.0


class CheckResult(BaseModel):
    name: str
    command: str
    status: CheckStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class VerificationReport(BaseModel):
    verdict: VerificationVerdict
    checks: list[CheckResult]
    summary: str
    unsafe_claim_detected: bool = False
    counterexample: dict[str, Any] | str | None = None
    changed_files: list[str] = Field(default_factory=list)
    failure_mode_ledger: list[str] = Field(default_factory=list)
    verification_ledger: list[str] = Field(default_factory=list)
    check_policy: dict[str, dict[str, Any]] = Field(default_factory=dict)


class AttemptRecord(BaseModel):
    attempt: int
    candidate_id: str | None = None
    candidate_role: Literal["primary", "alternate"] | None = None
    prompt: str
    evidence: str | None = None
    model_response: ModelResponse
    verification: VerificationReport
    usage: ModelUsage = Field(default_factory=ModelUsage)
    adapter_failure_reason: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime = Field(default_factory=utc_now)


class CandidateResult(BaseModel):
    candidate_id: str
    candidate_role: Literal["primary", "alternate"]
    attempt: int
    prompt: str
    model_response: ModelResponse
    verification: VerificationReport
    workspace_dir: Path
    diff_summary: dict[str, Any] = Field(default_factory=dict)
    risk_artifact: dict[str, Any] = Field(default_factory=dict)
    score: CandidateScore = Field(default_factory=CandidateScore)
    selected: bool = False


class RetryTranscript(BaseModel):
    run_id: str
    attempts: list[AttemptRecord]


class ProofCard(BaseModel):
    run_id: str
    task_id: str
    mode: Literal["baseline", "treatment", "review"]
    verdict: VerificationVerdict
    unsafe_claims: int
    attempts: int
    summary: str
    proof_points: list[str]
    artifact_dir: Path


class RunLedger(BaseModel):
    run_id: str
    task_id: str
    title: str
    mode: Literal["baseline", "treatment", "review"]
    controller_mode: Literal["sequential", "gearbox"] = "sequential"
    selected_candidate_id: str | None = None
    verdict: VerificationVerdict
    adapter: str
    artifact_dir: Path
    workspace_dir: Path
    plan: PlanArtifact
    attempts: list[AttemptRecord]
    candidate_results: list[CandidateResult] = Field(default_factory=list)
    unsafe_claims: int = 0
    model_calls_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    adapter_failure_reasons: list[str] = Field(default_factory=list)
    final_summary: str
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime = Field(default_factory=utc_now)

    @property
    def elapsed_seconds(self) -> float:
        return (self.ended_at - self.started_at).total_seconds()


class ReviewReport(BaseModel):
    verdict: Literal["APPROVE", "NEEDS_CHANGES", "UNSAFE"]
    summary: str
    risks: list[str] = Field(default_factory=list)
    supporting_checks: list[str] = Field(default_factory=list)


class MergeGateVerdict(BaseModel):
    allowed: bool
    summary: str
    reasons: list[str] = Field(default_factory=list)


class BenchmarkTaskResult(BaseModel):
    task_id: str
    mode: Literal["baseline", "treatment"]
    verdict: VerificationVerdict
    verified_success: bool
    unsafe_claims: int
    retries: int
    elapsed_seconds: float
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    artifact_dir: Path


class BenchmarkMetrics(BaseModel):
    verified_success_rate: float
    unsafe_claim_rate: float
    average_retries: float
    average_elapsed_seconds: float
    average_total_tokens: float = 0.0
    average_estimated_cost_usd: float = 0.0


class BenchmarkComparison(BaseModel):
    contract: dict[str, str] = Field(default_factory=lambda: contract_metadata(BENCHMARK_COMPARISON_KIND))
    benchmark_id: str
    config_path: Path
    task_results: list[BenchmarkTaskResult]
    baseline_metrics: BenchmarkMetrics
    treatment_metrics: BenchmarkMetrics
    delta_verified_success_rate: float
    delta_unsafe_claim_rate: float
    created_at: datetime = Field(default_factory=utc_now)
    report_dir: Path


class ControllerBenchmarkTaskResult(BaseModel):
    task_id: str
    controller_mode: Literal["sequential", "gearbox"]
    verdict: VerificationVerdict
    verified_success: bool
    unsafe_claims: int
    retries: int
    elapsed_seconds: float
    model_calls_used: int
    candidate_evaluations: int
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    selected_candidate_id: str | None = None
    artifact_dir: Path


class ControllerBenchmarkMetrics(BaseModel):
    verified_success_rate: float
    unsafe_claim_rate: float
    average_retries: float
    average_elapsed_seconds: float
    average_model_calls: float
    average_candidate_evaluations: float
    average_total_tokens: float = 0.0
    average_estimated_cost_usd: float = 0.0


class ControllerDecision(BaseModel):
    recommended_controller: Literal["sequential", "gearbox"]
    rationale: str
    should_promote_to_default: bool


class ControllerBenchmarkComparison(BaseModel):
    contract: dict[str, str] = Field(default_factory=lambda: contract_metadata(CONTROLLER_COMPARISON_KIND))
    benchmark_id: str
    config_path: Path
    task_results: list[ControllerBenchmarkTaskResult]
    sequential_metrics: ControllerBenchmarkMetrics
    gearbox_metrics: ControllerBenchmarkMetrics
    delta_verified_success_rate: float
    delta_unsafe_claim_rate: float
    delta_average_retries: float
    delta_average_elapsed_seconds: float
    delta_average_model_calls: float
    decision: ControllerDecision
    created_at: datetime = Field(default_factory=utc_now)
    report_dir: Path


class PocArm(str, Enum):
    RAW_CODEX = "raw_codex"
    CBC_BASELINE = "cbc_baseline"
    CBC_TREATMENT = "cbc_treatment"


class PocRunResult(BaseModel):
    task_id: str
    task_path: Path
    title: str
    arm: PocArm
    repetition: int
    verdict: VerificationVerdict
    verified_success: bool
    unsafe_claims: int
    retries: int
    elapsed_seconds: float
    changed_files: int
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    artifact_dir: Path
    summary: str


class ConfidenceInterval(BaseModel):
    low: float
    high: float


class PocMetrics(BaseModel):
    total_runs: int
    verified_successes: int
    unsafe_claim_runs: int
    verified_success_rate: float
    verified_success_ci: ConfidenceInterval
    unsafe_claim_rate: float
    unsafe_claim_ci: ConfidenceInterval
    average_retries: float
    average_elapsed_seconds: float
    average_changed_files: float
    average_total_tokens: float = 0.0
    average_estimated_cost_usd: float = 0.0


class PocWinLossTie(BaseModel):
    wins: int
    losses: int
    ties: int
    win_rate: float
    loss_rate: float
    tie_rate: float


class PocPairwiseSummary(BaseModel):
    left_arm: PocArm
    right_arm: PocArm
    total_pairs: int
    verified_success_rate_delta: float
    verified_success_rate_ci: ConfidenceInterval
    verified_success_outcomes: PocWinLossTie
    unsafe_claim_rate_reduction: float
    unsafe_claim_rate_reduction_ci: ConfidenceInterval
    safer_outcomes: PocWinLossTie


class PocComparison(BaseModel):
    poc_id: str
    config_path: Path
    seed: int
    sample_size: int
    repetitions: int
    raw_prompt_style: Literal["minimal", "scaffolded"]
    sampled_tasks: list[Path]
    results: list[PocRunResult]
    raw_codex_metrics: PocMetrics
    cbc_baseline_metrics: PocMetrics
    cbc_treatment_metrics: PocMetrics
    pairwise_summaries: list[PocPairwiseSummary]
    created_at: datetime = Field(default_factory=utc_now)
    report_dir: Path
