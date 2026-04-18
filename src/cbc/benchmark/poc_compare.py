from __future__ import annotations

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
    PocArm,
    PocComparison,
    PocMetrics,
    PocRunResult,
    TaskSpec,
    VerificationReport,
    VerificationVerdict,
)
from cbc.storage.artifacts import create_artifact_dir, write_json, write_markdown
from cbc.verify.core import verify_workspace
from cbc.workspace.diffing import summarize_workspace_diff
from cbc.workspace.staging import stage_workspace


class RawPromptStyle(str, Enum):
    MINIMAL = "minimal"
    SCAFFOLDED = "scaffolded"


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

    workspace = stage_workspace(task.workspace)
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


def run_cbc_arm(
    *,
    task: TaskSpec,
    task_path: Path,
    mode: str,
    repetition: int,
    config: AppConfig,
) -> PocRunResult:
    ledger = run_task(task, mode=mode, config=config)
    diff_summary = summarize_workspace_diff(task.workspace, ledger.workspace_dir)
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
        artifact_dir=ledger.artifact_dir,
        summary=ledger.final_summary,
    )


def compute_poc_metrics(results: list[PocRunResult]) -> PocMetrics:
    if not results:
        return PocMetrics(
            verified_success_rate=0.0,
            unsafe_claim_rate=0.0,
            average_retries=0.0,
            average_elapsed_seconds=0.0,
            average_changed_files=0.0,
        )

    total = len(results)
    return PocMetrics(
        verified_success_rate=sum(1 for result in results if result.verified_success) / total,
        unsafe_claim_rate=sum(1 for result in results if result.unsafe_claims > 0) / total,
        average_retries=sum(result.retries for result in results) / total,
        average_elapsed_seconds=sum(result.elapsed_seconds for result in results) / total,
        average_changed_files=sum(result.changed_files for result in results) / total,
    )


def run_poc_comparison(
    config_path: Path,
    *,
    seed: int,
    sample_size: int,
    repetitions: int,
    raw_prompt_style: RawPromptStyle = RawPromptStyle.SCAFFOLDED,
    config: AppConfig = DEFAULT_CONFIG,
) -> PocComparison:
    benchmark_config = load_benchmark_config(config_path)
    effective_config = apply_benchmark_config(config, benchmark_config)
    sampled_task_paths = sample_task_paths(benchmark_config.task_paths, sample_size=sample_size, seed=seed)

    report_dir = create_artifact_dir(effective_config.paths.reports_dir, "poc")
    artifact_root = effective_config.paths.artifacts_dir / "poc" / report_dir.name
    artifact_root.mkdir(parents=True, exist_ok=True)

    results: list[PocRunResult] = []
    for repetition in range(1, repetitions + 1):
        for task_path in sampled_task_paths:
            task = load_task(task_path)
            results.append(
                run_raw_codex_arm(
                    task=task,
                    task_path=task_path,
                    config=effective_config,
                    prompt_style=raw_prompt_style,
                    repetition=repetition,
                    artifact_root=artifact_root,
                )
            )
            results.append(run_cbc_arm(task=task, task_path=task_path, mode="baseline", repetition=repetition, config=effective_config))
            results.append(run_cbc_arm(task=task, task_path=task_path, mode="treatment", repetition=repetition, config=effective_config))

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
        report_dir=report_dir,
    )
    save_poc_report(comparison)
    return comparison


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
            "| Arm | Verified Success | Unsafe Claim | Avg Retries | Avg Seconds | Avg Changed Files |",
            "| --- | --- | --- | --- | --- | --- |",
            *[
                f"| `{arm}` | `{metrics.verified_success_rate:.2f}` | `{metrics.unsafe_claim_rate:.2f}` | "
                f"`{metrics.average_retries:.2f}` | `{metrics.average_elapsed_seconds:.2f}` | `{metrics.average_changed_files:.2f}` |"
                for arm, metrics in metric_rows
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
