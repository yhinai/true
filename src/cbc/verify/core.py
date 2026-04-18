from __future__ import annotations

import shutil
from pathlib import Path

from cbc.models import CheckResult, CheckStatus, VerificationReport, VerificationVerdict
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
from cbc.verify.type_runner import run_typecheck


def verify_workspace(
    workspace: Path,
    *,
    oracles,
    changed_files: list[str],
    claimed_success: bool,
    enable_deeper_checks: bool = False,
) -> VerificationReport:
    for cache_dir in workspace.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)

    checks: list[CheckResult] = [run_oracle(workspace, oracle) for oracle in oracles]
    checks.append(run_lint(workspace))
    checks.append(run_typecheck(workspace, enabled=False))
    checks.append(run_coverage(workspace, enabled=False))
    checks.append(inspect_contracts(workspace))
    checks.append(run_crosshair(workspace, enabled=enable_deeper_checks))
    checks.append(run_hypothesis(workspace, enabled=enable_deeper_checks))
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
