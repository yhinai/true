from __future__ import annotations

import json
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
    artifact_dir: Path | None = None,
) -> VerificationReport:
    for cache_dir in workspace.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)

    selected = _normalize_requested_checks(requested_checks)
    check_policy = _build_check_policy(task, changed_files=changed_files, selected=selected)
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
        checks.append(
            run_crosshair(
                workspace,
                enabled="python" in task.tags and task.verification.crosshair_enabled,
                command=task.verification.crosshair_command,
                skip_reason=str(check_policy["crosshair"]["reason"]),
            )
        )
    if _should_run(selected, "hypothesis"):
        checks.append(
            run_hypothesis(
                workspace,
                enabled="python" in task.tags,
                spec=task.hypothesis,
                artifact_dir=artifact_dir,
                skip_reason=str(check_policy["hypothesis"]["reason"]),
            )
        )
    if _should_run(selected, "mutation"):
        checks.append(
            run_mutation(
                workspace,
                enabled=task.verification.mutation_enabled,
                command=task.verification.mutation_command,
                skip_reason=str(check_policy["mutation"]["reason"]),
            )
        )

    verdict = verdict_from_checks(checks)
    failed_checks = [check for check in checks if check.status == CheckStatus.FAILED]
    counterexample = None
    if failed_checks:
        first = failed_checks[0]
        structured = first.details.get("counterexample")
        if structured is not None:
            counterexample = structured
        else:
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
        check_policy=check_policy,
    )


def format_counterexample(counterexample: dict[str, object] | str | None) -> str:
    if counterexample is None:
        return ""
    if isinstance(counterexample, str):
        return counterexample
    return json.dumps(counterexample, indent=2, sort_keys=True)


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


def _build_check_policy(
    task: TaskSpec,
    *,
    changed_files: list[str],
    selected: set[str] | None,
) -> dict[str, dict[str, object]]:
    python_tagged = "python" in task.tags
    likely_python_task = python_tagged or any(path.endswith(".py") for path in [*changed_files, *task.allowed_files])
    policy: dict[str, dict[str, object]] = {}

    for oracle in task.oracles:
        requested = _should_run_oracle(selected, oracle.name, oracle.kind)
        policy[f"oracle:{oracle.name}"] = _policy_entry(
            requested=requested,
            enabled=requested,
            reason="configured_task_oracle" if requested else "not_requested_for_this_run",
        )

    policy["lint"] = _requested_policy(selected, "lint", enabled=True, reason="always_on")
    policy["typecheck"] = _requested_policy(
        selected,
        "typecheck",
        enabled=task.verification.typecheck_enabled,
        reason="task_configured" if task.verification.typecheck_enabled else "disabled_in_task_config",
    )
    policy["coverage"] = _requested_policy(
        selected,
        "coverage",
        enabled=task.verification.coverage_enabled and bool(task.verification.coverage_command),
        reason=(
            "task_configured_command"
            if task.verification.coverage_enabled and task.verification.coverage_command
            else "missing_command"
            if task.verification.coverage_enabled
            else "disabled_in_task_config"
        ),
    )
    policy["structural"] = _requested_policy(
        selected,
        "structural",
        enabled=any(path.endswith(".py") for path in changed_files),
        reason="requires_changed_python_files",
    )
    policy["contracts"] = _requested_policy(
        selected,
        "contracts",
        enabled=likely_python_task,
        reason="static_workspace_inspection" if likely_python_task else "no_python_files_in_scope",
    )
    policy["crosshair"] = _requested_policy(
        selected,
        "crosshair",
        enabled=python_tagged and task.verification.crosshair_enabled and bool(task.verification.crosshair_command),
        reason=_crosshair_reason(task, python_tagged),
    )
    policy["hypothesis"] = _requested_policy(
        selected,
        "hypothesis",
        enabled=python_tagged and task.hypothesis is not None,
        reason="configured_property_cases" if python_tagged and task.hypothesis is not None else (
            "missing_spec" if python_tagged else "requires_python_tag"
        ),
    )
    policy["mutation"] = _requested_policy(
        selected,
        "mutation",
        enabled=task.verification.mutation_enabled and bool(task.verification.mutation_command),
        reason=(
            "task_configured_command"
            if task.verification.mutation_enabled and task.verification.mutation_command
            else "missing_command"
            if task.verification.mutation_enabled
            else "disabled_in_task_config"
        ),
    )
    return policy


def _requested_policy(
    selected: set[str] | None,
    check_name: str,
    *,
    enabled: bool,
    reason: str,
) -> dict[str, object]:
    requested = _should_run(selected, check_name)
    if not requested:
        return _policy_entry(requested=False, enabled=False, reason="not_requested_for_this_run")
    return _policy_entry(requested=True, enabled=enabled, reason=reason)


def _policy_entry(*, requested: bool, enabled: bool, reason: str) -> dict[str, object]:
    return {"requested": requested, "enabled": enabled, "reason": reason}


def _crosshair_reason(task: TaskSpec, python_tagged: bool) -> str:
    if not python_tagged:
        return "requires_python_tag"
    if not task.verification.crosshair_enabled:
        return "disabled_in_task_config"
    if not task.verification.crosshair_command:
        return "missing_command"
    return "task_configured_command"
