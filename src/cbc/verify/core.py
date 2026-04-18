from __future__ import annotations

import shutil
from pathlib import Path

from cbc.models import CheckResult, CheckStatus, TaskSpec, VerificationReport, VerificationVerdict
from cbc.verify.contract_ir import build_contract_graph
from cbc.verify.contracts import inspect_contracts
from cbc.verify.coverage_runner import run_coverage
from cbc.verify.crosshair_runner import run_crosshair
from cbc.verify.failure_modes import derive_failure_modes
from cbc.verify.hypothesis_runner import run_hypothesis
from cbc.verify.ledgers import build_verification_ledger
from cbc.verify.lint_runner import run_lint
from cbc.verify.mutation_runner import run_mutation
from cbc.verify.oracle_runner import run_oracle
from cbc.verify.policies import verdict_from_checks
from cbc.verify.structural_runner import run_structural
from cbc.verify.type_runner import run_typecheck


def verify_workspace(
    workspace: Path,
    *,
    task: TaskSpec,
    changed_files: list[str],
    claimed_success: bool,
    requested_checks: list[str] | None = None,
) -> VerificationReport:
    for cache_dir in workspace.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)

    selected = _normalize_requested_checks(requested_checks)
    checks: list[CheckResult] = []
    for oracle in task.oracles:
        if _should_run_oracle(selected, oracle.name, oracle.kind):
            checks.append(run_oracle(workspace, oracle))
    if _should_run(selected, "lint"):
        checks.append(run_lint(workspace, command=task.verification.lint_command))
    if _should_run(selected, "typecheck"):
        checks.append(
            run_typecheck(
                workspace,
                enabled=task.verification.typecheck_enabled,
                command=task.verification.typecheck_command,
            )
        )
    if _should_run(selected, "coverage"):
        checks.append(
            run_coverage(
                workspace,
                enabled=task.verification.coverage_enabled,
                command=task.verification.coverage_command,
            )
        )
    if _should_run(selected, "structural"):
        checks.append(run_structural(workspace, changed_files=changed_files))
    if _should_run(selected, "contracts"):
        checks.append(inspect_contracts(workspace))
    if _should_run(selected, "crosshair"):
        checks.append(run_crosshair(workspace, enabled="python" in task.tags))
    if _should_run(selected, "hypothesis"):
        checks.append(run_hypothesis(workspace, enabled="python" in task.tags))
    if _should_run(selected, "mutation"):
        checks.append(run_mutation(workspace, enabled=False))

    verdict = verdict_from_checks(checks)
    failed_checks = [check for check in checks if check.status == CheckStatus.FAILED]
    counterexample = None
    if failed_checks:
        first = failed_checks[0]
        counterexample = (first.stderr or first.stdout).strip()[:1500] or f"{first.name} failed"

    unsafe_claim = claimed_success and verdict != VerificationVerdict.VERIFIED
    verification_ledger = build_verification_ledger(checks)
    verification_ledger.extend([f"contract_graph_nodes={len(build_contract_graph(workspace))}"])

    return VerificationReport(
        verdict=verdict,
        checks=checks,
        summary="All deterministic checks passed." if verdict == VerificationVerdict.VERIFIED else "Deterministic verification failed or stayed unproven.",
        unsafe_claim_detected=unsafe_claim,
        counterexample=counterexample,
        changed_files=changed_files,
        failure_mode_ledger=derive_failure_modes(checks),
        verification_ledger=verification_ledger,
    )


def _normalize_requested_checks(requested_checks: list[str] | None) -> set[str] | None:
    if not requested_checks:
        return None
    selected = {item.strip().lower() for item in requested_checks if item.strip()}
    selected.update({"oracle", "lint"})
    return selected


def _should_run(selected: set[str] | None, check_name: str) -> bool:
    if selected is None:
        return True
    return check_name in selected


def _should_run_oracle(selected: set[str] | None, oracle_name: str, oracle_kind: str) -> bool:
    if selected is None:
        return True
    normalized_name = oracle_name.lower()
    normalized_kind = oracle_kind.lower()
    return any(name in selected for name in {"oracle", normalized_name, normalized_kind})
