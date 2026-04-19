from __future__ import annotations

import json
import math
import subprocess
import time
from enum import Enum
from pathlib import Path
from random import Random
from uuid import uuid4

from cbc.benchmark.local_runner import apply_benchmark_config, load_benchmark_config
from cbc.config import AppConfig, CodexConfig, DEFAULT_CONFIG
from cbc.controller.orchestrator import resolve_codex_config, run_task
from cbc.graph.mismatch import find_scope_mismatches
from cbc.intake.normalize import load_task
from cbc.models import (
    CheckResult,
    CheckStatus,
    ConfidenceInterval,
    PocArm,
    PocComparison,
    PocMetrics,
    PocPairwiseSummary,
    PocRunResult,
    PocWinLossTie,
    TaskSpec,
    VerificationReport,
    VerificationVerdict,
)
from cbc.storage.artifacts import create_artifact_dir, write_json, write_markdown
from cbc.verify.core import verify_workspace
from cbc.workspace.diffing import summarize_workspace_diff
from cbc.workspace.staging import create_workspace_lease


class RawPromptStyle(str, Enum):
    MINIMAL = "minimal"
    SCAFFOLDED = "scaffolded"


PAIRWISE_ARM_ORDER: list[tuple[PocArm, PocArm]] = [
    (PocArm.CBC_BASELINE, PocArm.RAW_CODEX),
    (PocArm.CBC_TREATMENT, PocArm.RAW_CODEX),
    (PocArm.CBC_TREATMENT, PocArm.CBC_BASELINE),
]


def sample_task_paths(task_paths: list[Path], *, sample_size: int, seed: int) -> list[Path]:
    ordered = sorted(path.resolve() for path in task_paths)
    if sample_size >= len(ordered):
        return ordered
    rng = Random(seed)
    return rng.sample(ordered, k=sample_size)


def build_raw_codex_prompt(task: TaskSpec, *, prompt_style: RawPromptStyle) -> str:
    if prompt_style == RawPromptStyle.MINIMAL:
        return task.prompt

    lines = [
        "You are running directly in the workspace without the CBC retry loop.",
        "Edit files in place and stop when done.",
        "",
        f"Task:\n{task.prompt}",
        "",
        f"Allowed files: {', '.join(task.allowed_files) if task.allowed_files else '(none specified)'}",
        f"Required checks: {', '.join(task.required_checks) if task.required_checks else '(task oracle only)'}",
    ]
    if task.doubt_points:
        lines.append(f"Doubt points: {', '.join(task.doubt_points)}")
    if task.hypothesis is not None and task.hypothesis.cases:
        lines.append(f"Property cases: {', '.join(str(case) for case in task.hypothesis.cases)}")
    return "\n".join(lines)


def run_raw_codex_arm(
    *,
    task: TaskSpec,
    task_path: Path,
    config: AppConfig,
    prompt_style: RawPromptStyle,
    repetition: int,
    artifact_root: Path,
) -> PocRunResult:
    artifact_dir = artifact_root / f"{task.task_id}-rep{repetition}" / PocArm.RAW_CODEX.value
    artifact_dir.mkdir(parents=True, exist_ok=True)

    workspace_lease = create_workspace_lease(task.workspace)
    try:
        workspace = workspace_lease.path
        raw_config = resolve_codex_config(task, config)
        prompt = build_raw_codex_prompt(task, prompt_style=prompt_style)
        command = _build_raw_codex_command(raw_config, workspace)

        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed_seconds = time.monotonic() - started

        diff_summary = summarize_workspace_diff(task.workspace, workspace)
        changed_files = [entry["path"] for entry in diff_summary["files"] if isinstance(entry.get("path"), str)]
        verification = verify_workspace(
            workspace,
            task=task,
            changed_files=changed_files,
            claimed_success=completed.returncode == 0,
            artifact_dir=artifact_dir,
        )
        scope_mismatches = find_scope_mismatches(changed_files, task.allowed_files)
        verification = _apply_scope_guard(verification, scope_mismatches, claimed_success=completed.returncode == 0)

        raw_artifact = {
            "task_id": task.task_id,
            "task_path": str(task_path),
            "arm": PocArm.RAW_CODEX.value,
            "prompt_style": prompt_style.value,
            "command": command,
            "exit_code": completed.returncode,
            "prompt": prompt,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "diff_summary": diff_summary,
            "scope_mismatches": scope_mismatches,
            "verification": verification.model_dump(mode="json"),
        }
        write_json(artifact_dir / "raw_codex_artifact.json", raw_artifact)
        write_markdown(artifact_dir / "summary.md", render_raw_codex_markdown(raw_artifact))

        return PocRunResult(
            task_id=task.task_id,
            task_path=task_path.resolve(),
            title=task.title,
            arm=PocArm.RAW_CODEX,
            repetition=repetition,
            verdict=verification.verdict,
            verified_success=verification.verdict == VerificationVerdict.VERIFIED,
            unsafe_claims=int(verification.unsafe_claim_detected),
            retries=0,
            elapsed_seconds=elapsed_seconds,
            changed_files=diff_summary["total_files"],
            artifact_dir=artifact_dir,
            summary=verification.summary,
        )
    finally:
        workspace_lease.cleanup()


def run_cbc_arm(
    *,
    task: TaskSpec,
    task_path: Path,
    mode: str,
    repetition: int,
    config: AppConfig,
) -> PocRunResult:
    ledger = run_task(task, mode=mode, config=config)
    diff_summary = _load_diff_summary(ledger.artifact_dir)
    arm = PocArm.CBC_BASELINE if mode == "baseline" else PocArm.CBC_TREATMENT
    return PocRunResult(
        task_id=task.task_id,
        task_path=task_path.resolve(),
        title=task.title,
        arm=arm,
        repetition=repetition,
        verdict=ledger.verdict,
        verified_success=ledger.verdict == VerificationVerdict.VERIFIED,
        unsafe_claims=ledger.unsafe_claims,
        retries=max(len(ledger.attempts) - 1, 0),
        elapsed_seconds=ledger.elapsed_seconds,
        changed_files=diff_summary["total_files"],
        total_tokens=ledger.total_tokens,
        estimated_cost_usd=ledger.estimated_cost_usd,
        artifact_dir=ledger.artifact_dir,
        summary=ledger.final_summary,
    )


def run_simulated_raw_arm(
    *,
    task: TaskSpec,
    task_path: Path,
    repetition: int,
    config: AppConfig,
) -> PocRunResult:
    ledger = run_task(task, mode="baseline", config=config)
    diff_summary = _load_diff_summary(ledger.artifact_dir)
    return PocRunResult(
        task_id=task.task_id,
        task_path=task_path.resolve(),
        title=task.title,
        arm=PocArm.RAW_CODEX,
        repetition=repetition,
        verdict=ledger.verdict,
        verified_success=ledger.verdict == VerificationVerdict.VERIFIED,
        unsafe_claims=ledger.unsafe_claims,
        retries=max(len(ledger.attempts) - 1, 0),
        elapsed_seconds=ledger.elapsed_seconds,
        changed_files=diff_summary["total_files"],
        total_tokens=ledger.total_tokens,
        estimated_cost_usd=ledger.estimated_cost_usd,
        artifact_dir=ledger.artifact_dir,
        summary=f"simulated raw-agent baseline: {ledger.final_summary}",
    )


def compute_poc_metrics(results: list[PocRunResult]) -> PocMetrics:
    if not results:
        return PocMetrics(
            total_runs=0,
            verified_successes=0,
            unsafe_claim_runs=0,
            verified_success_rate=0.0,
            verified_success_ci=ConfidenceInterval(low=0.0, high=0.0),
            unsafe_claim_rate=0.0,
            unsafe_claim_ci=ConfidenceInterval(low=0.0, high=0.0),
            average_retries=0.0,
            average_elapsed_seconds=0.0,
            average_changed_files=0.0,
        )

    total = len(results)
    verified_successes = sum(1 for result in results if result.verified_success)
    unsafe_claim_runs = sum(1 for result in results if result.unsafe_claims > 0)
    return PocMetrics(
        total_runs=total,
        verified_successes=verified_successes,
        unsafe_claim_runs=unsafe_claim_runs,
        verified_success_rate=verified_successes / total,
        verified_success_ci=_proportion_confidence_interval(verified_successes, total),
        unsafe_claim_rate=unsafe_claim_runs / total,
        unsafe_claim_ci=_proportion_confidence_interval(unsafe_claim_runs, total),
        average_retries=sum(result.retries for result in results) / total,
        average_elapsed_seconds=sum(result.elapsed_seconds for result in results) / total,
        average_changed_files=sum(result.changed_files for result in results) / total,
        average_total_tokens=sum(result.total_tokens for result in results) / total,
        average_estimated_cost_usd=sum(result.estimated_cost_usd or 0.0 for result in results) / total,
    )


def build_pairwise_summary(
    results: list[PocRunResult],
    *,
    left_arm: PocArm,
    right_arm: PocArm,
) -> PocPairwiseSummary:
    left_by_key = {
        (result.task_id, result.repetition): result for result in results if result.arm == left_arm
    }
    right_by_key = {
        (result.task_id, result.repetition): result for result in results if result.arm == right_arm
    }
    if left_by_key.keys() != right_by_key.keys():
        missing_left = sorted(right_by_key.keys() - left_by_key.keys())
        missing_right = sorted(left_by_key.keys() - right_by_key.keys())
        raise ValueError(
            "Paired POC comparison requires balanced task/repetition pairs; "
            f"missing in {left_arm.value}: {missing_left}, missing in {right_arm.value}: {missing_right}"
        )
    shared_keys = sorted(left_by_key.keys() & right_by_key.keys())
    if not shared_keys:
        return PocPairwiseSummary(
            left_arm=left_arm,
            right_arm=right_arm,
            total_pairs=0,
            verified_success_rate_delta=0.0,
            verified_success_rate_ci=ConfidenceInterval(low=0.0, high=0.0),
            verified_success_outcomes=PocWinLossTie(
                wins=0,
                losses=0,
                ties=0,
                win_rate=0.0,
                loss_rate=0.0,
                tie_rate=0.0,
            ),
            unsafe_claim_rate_reduction=0.0,
            unsafe_claim_rate_reduction_ci=ConfidenceInterval(low=0.0, high=0.0),
            safer_outcomes=PocWinLossTie(
                wins=0,
                losses=0,
                ties=0,
                win_rate=0.0,
                loss_rate=0.0,
                tie_rate=0.0,
            ),
        )

    success_differences: list[float] = []
    unsafe_reductions: list[float] = []
    success_outcomes: list[int] = []
    safety_outcomes: list[int] = []
    for key in shared_keys:
        left = left_by_key[key]
        right = right_by_key[key]
        left_success = int(left.verified_success)
        right_success = int(right.verified_success)
        left_unsafe = int(left.unsafe_claims > 0)
        right_unsafe = int(right.unsafe_claims > 0)

        success_differences.append(float(left_success - right_success))
        unsafe_reductions.append(float(right_unsafe - left_unsafe))
        success_outcomes.append(_cmp(left_success, right_success))
        safety_outcomes.append(_cmp(right_unsafe, left_unsafe))

    return PocPairwiseSummary(
        left_arm=left_arm,
        right_arm=right_arm,
        total_pairs=len(shared_keys),
        verified_success_rate_delta=sum(success_differences) / len(success_differences),
        verified_success_rate_ci=_mean_confidence_interval(success_differences, minimum=-1.0, maximum=1.0),
        verified_success_outcomes=_summarize_outcomes(success_outcomes),
        unsafe_claim_rate_reduction=sum(unsafe_reductions) / len(unsafe_reductions),
        unsafe_claim_rate_reduction_ci=_mean_confidence_interval(unsafe_reductions, minimum=-1.0, maximum=1.0),
        safer_outcomes=_summarize_outcomes(safety_outcomes),
    )


def run_poc_comparison(
    config_path: Path,
    *,
    seed: int,
    sample_size: int,
    repetitions: int,
    raw_prompt_style: RawPromptStyle = RawPromptStyle.SCAFFOLDED,
    simulated: bool = False,
    config: AppConfig = DEFAULT_CONFIG,
    progress: object | None = None,
) -> PocComparison:
    benchmark_config = load_benchmark_config(config_path)
    effective_config = apply_benchmark_config(config, benchmark_config)
    sampled_task_paths = sample_task_paths(benchmark_config.task_paths, sample_size=sample_size, seed=seed)

    report_dir = create_artifact_dir(effective_config.paths.reports_dir, "poc")
    artifact_root = effective_config.paths.artifacts_dir / "poc" / report_dir.name
    artifact_root.mkdir(parents=True, exist_ok=True)

    total_tasks = len(sampled_task_paths) * repetitions
    progress_task_id = None
    if progress is not None:
        progress_task_id = progress.add_task(
            f"Running {config_path.stem}", total=total_tasks
        )

    results: list[PocRunResult] = []
    step = 0
    for repetition in range(1, repetitions + 1):
        for task_path in sampled_task_paths:
            resolved_task_path = _resolve_poc_task_path(task_path, simulated=simulated)
            task = load_task(resolved_task_path)
            step += 1
            if progress is not None and progress_task_id is not None:
                progress.update(
                    progress_task_id,
                    description=f"{step}/{total_tasks} {task.task_id} rep{repetition}",
                )
            if simulated:
                results.append(
                    run_simulated_raw_arm(
                        task=task,
                        task_path=resolved_task_path,
                        repetition=repetition,
                        config=effective_config,
                    )
                )
            else:
                results.append(
                    run_raw_codex_arm(
                        task=task,
                        task_path=resolved_task_path,
                        config=effective_config,
                        prompt_style=raw_prompt_style,
                        repetition=repetition,
                        artifact_root=artifact_root,
                    )
                )
            results.append(run_cbc_arm(task=task, task_path=resolved_task_path, mode="baseline", repetition=repetition, config=effective_config))
            results.append(run_cbc_arm(task=task, task_path=resolved_task_path, mode="treatment", repetition=repetition, config=effective_config))
            if progress is not None and progress_task_id is not None:
                progress.advance(progress_task_id)

    comparison = PocComparison(
        poc_id=uuid4().hex[:12],
        config_path=config_path.resolve(),
        seed=seed,
        sample_size=len(sampled_task_paths),
        repetitions=repetitions,
        raw_prompt_style=raw_prompt_style.value,
        sampled_tasks=sampled_task_paths,
        results=results,
        raw_codex_metrics=compute_poc_metrics([result for result in results if result.arm == PocArm.RAW_CODEX]),
        cbc_baseline_metrics=compute_poc_metrics([result for result in results if result.arm == PocArm.CBC_BASELINE]),
        cbc_treatment_metrics=compute_poc_metrics([result for result in results if result.arm == PocArm.CBC_TREATMENT]),
        pairwise_summaries=[
            build_pairwise_summary(results, left_arm=left_arm, right_arm=right_arm)
            for left_arm, right_arm in PAIRWISE_ARM_ORDER
        ],
        report_dir=report_dir,
    )
    save_poc_report(comparison)
    return comparison


def _resolve_poc_task_path(task_path: Path, *, simulated: bool) -> Path:
    if not simulated:
        return task_path
    if task_path.parent.name.endswith("_codex"):
        sibling_dir = task_path.parent.with_name(task_path.parent.name.removesuffix("_codex"))
        sibling_task = sibling_dir / task_path.name
        if sibling_task.exists():
            return sibling_task
    return task_path


def _load_diff_summary(artifact_dir: Path) -> dict[str, object]:
    return json.loads((artifact_dir / "diff_summary.json").read_text(encoding="utf-8"))


def save_poc_report(comparison: PocComparison) -> None:
    comparison.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(comparison.report_dir / "comparison.json", comparison.model_dump(mode="json"))
    write_markdown(comparison.report_dir / "comparison.md", render_poc_markdown(comparison))


def render_poc_markdown(comparison: PocComparison) -> str:
    metric_rows = [
        ("raw_codex", comparison.raw_codex_metrics),
        ("cbc_baseline", comparison.cbc_baseline_metrics),
        ("cbc_treatment", comparison.cbc_treatment_metrics),
    ]
    metric_table = "\n".join(
        [
            "| Arm | Runs | Verified Success | 95% CI | Unsafe Claim | 95% CI | Avg Retries | Avg Seconds | Avg Changed Files |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| `{arm}` | `{metrics.total_runs}` | `{metrics.verified_success_rate:.2f}` | "
                f"`{_format_interval(metrics.verified_success_ci)}` | `{metrics.unsafe_claim_rate:.2f}` | "
                f"`{_format_interval(metrics.unsafe_claim_ci)}` | `{metrics.average_retries:.2f}` | "
                f"`{metrics.average_elapsed_seconds:.2f}` | `{metrics.average_changed_files:.2f}` |"
                for arm, metrics in metric_rows
            ],
        ]
    )
    pairwise_table = "\n".join(
        [
            "| Comparison | Pairs | Success Delta | 95% CI | Success W-L-T | Unsafe Reduction | 95% CI | Safer W-L-T |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| `{summary.left_arm.value} vs {summary.right_arm.value}` | `{summary.total_pairs}` | "
                f"`{summary.verified_success_rate_delta:.2f}` | `{_format_interval(summary.verified_success_rate_ci)}` | "
                f"`{_format_outcomes(summary.verified_success_outcomes)}` | "
                f"`{summary.unsafe_claim_rate_reduction:.2f}` | `{_format_interval(summary.unsafe_claim_rate_reduction_ci)}` | "
                f"`{_format_outcomes(summary.safer_outcomes)}` |"
                for summary in comparison.pairwise_summaries
            ],
        ]
    )
    sampled = "\n".join(f"- `{path.parent.name}` from `{path}`" for path in comparison.sampled_tasks)
    runs = "\n".join(
        [
            "| Task | Rep | Arm | Verdict | Unsafe Claims | Retries | Seconds | Changed Files |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| `{result.task_id}` | `{result.repetition}` | `{result.arm.value}` | `{result.verdict.value}` | "
                f"`{result.unsafe_claims}` | `{result.retries}` | `{result.elapsed_seconds:.2f}` | `{result.changed_files}` |"
                for result in comparison.results
            ],
        ]
    )
    return (
        "# POC Comparison\n\n"
        f"- Seed: `{comparison.seed}`\n"
        f"- Sample size: `{comparison.sample_size}`\n"
        f"- Repetitions: `{comparison.repetitions}`\n"
        f"- Raw prompt style: `{comparison.raw_prompt_style}`\n\n"
        "## Sampled Tasks\n"
        f"{sampled}\n\n"
        "## Arm Metrics\n"
        f"{metric_table}\n\n"
        "## Pairwise Scoreboard\n"
        f"{pairwise_table}\n\n"
        "## Run Matrix\n"
        f"{runs}\n"
    )


def render_raw_codex_markdown(raw_artifact: dict[str, object]) -> str:
    verification = raw_artifact["verification"]
    assert isinstance(verification, dict)
    scope_mismatches = raw_artifact.get("scope_mismatches", [])
    return (
        "# Raw Codex Run\n\n"
        f"- Task: `{raw_artifact['task_id']}`\n"
        f"- Prompt style: `{raw_artifact['prompt_style']}`\n"
        f"- Exit code: `{raw_artifact['exit_code']}`\n"
        f"- Verification verdict: `{verification['verdict']}`\n"
        f"- Scope mismatches: `{', '.join(scope_mismatches) if scope_mismatches else 'none'}`\n"
    )


def _build_raw_codex_command(config: CodexConfig, workspace: Path) -> list[str]:
    command = [
        config.executable,
        "exec",
        "--cd",
        str(workspace),
        "--sandbox",
        config.sandbox,
    ]
    if config.skip_git_repo_check:
        command.append("--skip-git-repo-check")
    if config.default_model:
        command.extend(["--model", config.default_model])
    if config.profile:
        command.extend(["--profile", config.profile])
    for override in config.config_overrides:
        command.extend(["--config", override])
    for add_dir in config.add_dirs:
        command.extend(["--add-dir", str(add_dir)])
    if config.dangerously_bypass_approvals:
        command.append("--dangerously-bypass-approvals-and-sandbox")
    command.append("-")
    return command


def _apply_scope_guard(
    verification: VerificationReport,
    scope_mismatches: list[str],
    *,
    claimed_success: bool,
) -> VerificationReport:
    if not scope_mismatches:
        return verification

    scope_check = CheckResult(
        name="scope",
        command="allowed_files",
        status=CheckStatus.FAILED,
        exit_code=1,
        stderr=f"Raw Codex modified files outside the allowed scope: {', '.join(scope_mismatches)}",
        details={"scope_mismatches": scope_mismatches},
    )
    return verification.model_copy(
        update={
            "verdict": VerificationVerdict.FALSIFIED,
            "checks": [*verification.checks, scope_check],
            "summary": "Deterministic verification failed because the raw Codex run wrote outside the allowed scope.",
            "unsafe_claim_detected": verification.unsafe_claim_detected or claimed_success,
            "counterexample": {"scope_mismatches": scope_mismatches},
            "failure_mode_ledger": [*verification.failure_mode_ledger, "scope_violation"],
            "verification_ledger": [*verification.verification_ledger, f"scope_mismatches={','.join(scope_mismatches)}"],
        }
    )


def _proportion_confidence_interval(successes: int, total: int, *, z: float = 1.959963984540054) -> ConfidenceInterval:
    if total <= 0:
        return ConfidenceInterval(low=0.0, high=0.0)

    proportion = successes / total
    denominator = 1.0 + (z * z) / total
    center = (proportion + (z * z) / (2.0 * total)) / denominator
    margin = (
        z
        * math.sqrt((proportion * (1.0 - proportion) + (z * z) / (4.0 * total)) / total)
        / denominator
    )
    return ConfidenceInterval(low=max(0.0, center - margin), high=min(1.0, center + margin))


def _mean_confidence_interval(
    values: list[float],
    *,
    minimum: float,
    maximum: float,
    z: float = 1.959963984540054,
) -> ConfidenceInterval:
    if not values:
        return ConfidenceInterval(low=0.0, high=0.0)

    mean = sum(values) / len(values)
    if len(values) == 1:
        return ConfidenceInterval(low=mean, high=mean)

    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    margin = z * math.sqrt(variance / len(values))
    return ConfidenceInterval(
        low=max(minimum, mean - margin),
        high=min(maximum, mean + margin),
    )


def _summarize_outcomes(outcomes: list[int]) -> PocWinLossTie:
    if not outcomes:
        return PocWinLossTie(wins=0, losses=0, ties=0, win_rate=0.0, loss_rate=0.0, tie_rate=0.0)

    total = len(outcomes)
    wins = sum(1 for outcome in outcomes if outcome > 0)
    losses = sum(1 for outcome in outcomes if outcome < 0)
    ties = total - wins - losses
    return PocWinLossTie(
        wins=wins,
        losses=losses,
        ties=ties,
        win_rate=wins / total,
        loss_rate=losses / total,
        tie_rate=ties / total,
    )


def _cmp(left: int, right: int) -> int:
    if left > right:
        return 1
    if left < right:
        return -1
    return 0


def _format_interval(interval: ConfidenceInterval) -> str:
    return f"{interval.low:.2f}-{interval.high:.2f}"


def _format_outcomes(outcomes: PocWinLossTie) -> str:
    return f"{outcomes.wins}-{outcomes.losses}-{outcomes.ties}"
