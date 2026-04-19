from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from cbc.benchmark.poc_compare import (
    RawPromptStyle,
    _resolve_poc_task_path,
    build_raw_codex_prompt,
    build_pairwise_summary,
    compute_poc_metrics,
    run_poc_comparison,
    run_raw_codex_arm,
    sample_task_paths,
)
from cbc.config import AppConfig, PathsConfig, RetryConfig
from cbc.models import OracleSpec, PocArm, PocRunResult, TaskSpec, VerificationVerdict


ROOT = Path(__file__).resolve().parents[1]


def build_test_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        paths=PathsConfig(
            root=ROOT,
            artifacts_dir=tmp_path / "artifacts",
            reports_dir=tmp_path / "reports",
            prompts_dir=ROOT / "prompts",
            benchmark_config_dir=ROOT / "benchmark-configs",
            storage_db=tmp_path / "artifacts" / "cbc.sqlite3",
        ),
        retry=RetryConfig(max_attempts=2),
    )


def make_poc_result(
    *,
    task_id: str,
    arm: PocArm,
    repetition: int,
    verified_success: bool,
    unsafe_claims: int,
    elapsed_seconds: float = 1.0,
) -> PocRunResult:
    return PocRunResult(
        task_id=task_id,
        task_path=ROOT / "fixtures" / f"{task_id}.yaml",
        title=task_id,
        arm=arm,
        repetition=repetition,
        verdict=VerificationVerdict.VERIFIED if verified_success else VerificationVerdict.FALSIFIED,
        verified_success=verified_success,
        unsafe_claims=unsafe_claims,
        retries=0,
        elapsed_seconds=elapsed_seconds,
        changed_files=1,
        artifact_dir=ROOT / "artifacts" / task_id / arm.value,
        summary=arm.value,
    )


def test_sample_task_paths_is_seeded_and_capped() -> None:
    task_paths = [Path(name) for name in ("a.yaml", "b.yaml", "c.yaml", "d.yaml")]
    resolved = sorted(path.resolve() for path in task_paths)

    first = sample_task_paths(task_paths, sample_size=2, seed=7)
    second = sample_task_paths(task_paths, sample_size=2, seed=7)
    capped = sample_task_paths(task_paths, sample_size=10, seed=7)

    assert first == second
    assert len(first) == 2
    assert capped == resolved


def test_build_raw_codex_prompt_supports_minimal_and_scaffolded() -> None:
    task = TaskSpec(
        task_id="demo",
        title="Demo task",
        prompt="Fix app.py",
        workspace=Path("/tmp/demo"),
        allowed_files=["app.py"],
        required_checks=["pytest"],
        doubt_points=["Keep the fix minimal."],
        adapter="codex",
        oracles=[OracleSpec(name="pytest", kind="pytest", command="-q")],
        tags=["python"],
    )

    minimal = build_raw_codex_prompt(task, prompt_style=RawPromptStyle.MINIMAL)
    scaffolded = build_raw_codex_prompt(task, prompt_style=RawPromptStyle.SCAFFOLDED)

    assert minimal == "Fix app.py"
    assert "Allowed files: app.py" in scaffolded
    assert "Required checks: pytest" in scaffolded
    assert "Doubt points: Keep the fix minimal." in scaffolded


def test_compute_poc_metrics_adds_counts_and_confidence_intervals() -> None:
    results = [
        make_poc_result(task_id="task-a", arm=PocArm.RAW_CODEX, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-b", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=1),
        make_poc_result(task_id="task-c", arm=PocArm.RAW_CODEX, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-d", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=0),
    ]

    metrics = compute_poc_metrics(results)

    assert metrics.total_runs == 4
    assert metrics.verified_successes == 2
    assert metrics.unsafe_claim_runs == 1
    assert metrics.verified_success_rate == 0.5
    assert metrics.unsafe_claim_rate == 0.25
    assert metrics.verified_success_ci.low <= metrics.verified_success_rate <= metrics.verified_success_ci.high
    assert metrics.unsafe_claim_ci.low <= metrics.unsafe_claim_rate <= metrics.unsafe_claim_ci.high


def test_build_pairwise_summary_counts_wins_losses_and_deltas() -> None:
    results = [
        make_poc_result(task_id="task-b", arm=PocArm.CBC_TREATMENT, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-a", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-c", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=0),
        make_poc_result(task_id="task-e", arm=PocArm.CBC_TREATMENT, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-d", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-a", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=1),
        make_poc_result(task_id="task-e", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=1),
        make_poc_result(task_id="task-c", arm=PocArm.CBC_TREATMENT, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-b", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=False, unsafe_claims=1),
        make_poc_result(task_id="task-d", arm=PocArm.CBC_TREATMENT, repetition=1, verified_success=False, unsafe_claims=1),
        make_poc_result(task_id="task-c", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=False, unsafe_claims=0),
        make_poc_result(task_id="task-a", arm=PocArm.CBC_TREATMENT, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-b", arm=PocArm.RAW_CODEX, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-d", arm=PocArm.RAW_CODEX, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-e", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=True, unsafe_claims=0),
    ]

    treatment_vs_raw = build_pairwise_summary(results, left_arm=PocArm.CBC_TREATMENT, right_arm=PocArm.RAW_CODEX)
    treatment_vs_baseline = build_pairwise_summary(results, left_arm=PocArm.CBC_TREATMENT, right_arm=PocArm.CBC_BASELINE)

    assert treatment_vs_raw.total_pairs == 5
    assert treatment_vs_raw.verified_success_outcomes.wins == 3
    assert treatment_vs_raw.verified_success_outcomes.losses == 1
    assert treatment_vs_raw.verified_success_outcomes.ties == 1
    assert treatment_vs_raw.verified_success_rate_delta == pytest.approx(0.4)
    assert treatment_vs_raw.safer_outcomes.wins == 2
    assert treatment_vs_raw.safer_outcomes.losses == 1
    assert treatment_vs_raw.safer_outcomes.ties == 2
    assert treatment_vs_raw.unsafe_claim_rate_reduction == pytest.approx(0.2)
    assert treatment_vs_raw.verified_success_rate_ci.low <= treatment_vs_raw.verified_success_rate_delta
    assert treatment_vs_raw.verified_success_rate_ci.high >= treatment_vs_raw.verified_success_rate_delta

    assert treatment_vs_baseline.total_pairs == 5
    assert treatment_vs_baseline.verified_success_outcomes.wins == 2
    assert treatment_vs_baseline.verified_success_outcomes.losses == 1
    assert treatment_vs_baseline.verified_success_outcomes.ties == 2
    assert treatment_vs_baseline.verified_success_rate_delta == pytest.approx(0.2)
    assert treatment_vs_baseline.safer_outcomes.wins == 1
    assert treatment_vs_baseline.safer_outcomes.losses == 1
    assert treatment_vs_baseline.safer_outcomes.ties == 3
    assert treatment_vs_baseline.unsafe_claim_rate_reduction == pytest.approx(0.0)


def test_build_pairwise_summary_all_ties_is_stable() -> None:
    results = []
    for task_id in ("task-a", "task-b", "task-c"):
        for arm in (PocArm.RAW_CODEX, PocArm.CBC_BASELINE):
            results.append(
                make_poc_result(task_id=task_id, arm=arm, repetition=1, verified_success=True, unsafe_claims=0)
            )

    summary = build_pairwise_summary(results, left_arm=PocArm.CBC_BASELINE, right_arm=PocArm.RAW_CODEX)

    assert summary.total_pairs == 3
    assert summary.verified_success_rate_delta == 0.0
    assert summary.unsafe_claim_rate_reduction == 0.0
    assert summary.verified_success_outcomes.wins == 0
    assert summary.verified_success_outcomes.losses == 0
    assert summary.verified_success_outcomes.ties == 3
    assert summary.verified_success_rate_ci.low == 0.0
    assert summary.verified_success_rate_ci.high == 0.0
    assert summary.unsafe_claim_rate_reduction_ci.low == 0.0
    assert summary.unsafe_claim_rate_reduction_ci.high == 0.0


def test_build_pairwise_summary_rejects_unbalanced_pairs() -> None:
    results = [
        make_poc_result(task_id="task-a", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=0),
        make_poc_result(task_id="task-a", arm=PocArm.CBC_BASELINE, repetition=1, verified_success=True, unsafe_claims=0),
        make_poc_result(task_id="task-b", arm=PocArm.RAW_CODEX, repetition=1, verified_success=False, unsafe_claims=0),
    ]

    with pytest.raises(ValueError, match="Paired POC comparison requires balanced task/repetition pairs"):
        build_pairwise_summary(results, left_arm=PocArm.CBC_BASELINE, right_arm=PocArm.RAW_CODEX)


def test_run_raw_codex_arm_marks_scope_violation_as_failure(monkeypatch, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (workspace / "test_app.py").write_text("def test_add():\n    assert True\n", encoding="utf-8")

    task = TaskSpec(
        task_id="scope_violation",
        title="Scope violation task",
        prompt="Fix app.py only.",
        workspace=workspace,
        allowed_files=["app.py"],
        required_checks=["pytest"],
        adapter="codex",
        oracles=[OracleSpec(name="oracle", kind="python", command='-c "print(\'ok\')"')],
        tags=["python"],
    )

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cwd = kwargs["cwd"]
        assert isinstance(cwd, Path)
        (cwd / "test_app.py").write_text("def test_add():\n    assert False\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_raw_codex_arm(
        task=task,
        task_path=tmp_path / "task.yaml",
        config=build_test_config(tmp_path),
        prompt_style=RawPromptStyle.SCAFFOLDED,
        repetition=1,
        artifact_root=tmp_path / "artifacts" / "poc",
    )

    assert result.arm == PocArm.RAW_CODEX
    assert result.verdict == VerificationVerdict.FALSIFIED
    assert result.unsafe_claims == 1
    assert result.changed_files == 1
    assert (result.artifact_dir / "raw_codex_artifact.json").exists()


def test_run_poc_comparison_writes_report_with_seeded_sample(monkeypatch, tmp_path: Path) -> None:
    task_a = tmp_path / "a.yaml"
    task_b = tmp_path / "b.yaml"
    config_path = tmp_path / "poc.yaml"
    config_path.write_text(f"tasks:\n  - {task_a}\n  - {task_b}\n", encoding="utf-8")

    def fake_raw(*, task, task_path, config, prompt_style, repetition, artifact_root):
        return PocRunResult(
            task_id=task.task_id,
            task_path=task_path,
            title=task.title,
            arm=PocArm.RAW_CODEX,
            repetition=repetition,
            verdict=VerificationVerdict.FALSIFIED,
            verified_success=False,
            unsafe_claims=1,
            retries=0,
            elapsed_seconds=1.0,
            changed_files=1,
            artifact_dir=artifact_root / f"{task.task_id}-raw",
            summary="raw failed",
        )

    def fake_cbc(*, task, task_path, mode, repetition, config):
        arm = PocArm.CBC_BASELINE if mode == "baseline" else PocArm.CBC_TREATMENT
        verified = mode == "treatment"
        return PocRunResult(
            task_id=task.task_id,
            task_path=task_path,
            title=task.title,
            arm=arm,
            repetition=repetition,
            verdict=VerificationVerdict.VERIFIED if verified else VerificationVerdict.FALSIFIED,
            verified_success=verified,
            unsafe_claims=0 if verified else 1,
            retries=0 if mode == "baseline" else 1,
            elapsed_seconds=2.0 if mode == "baseline" else 3.0,
            changed_files=1,
            artifact_dir=tmp_path / "artifacts" / mode,
            summary=mode,
        )

    def fake_load_task(path: Path) -> TaskSpec:
        return TaskSpec(
            task_id=path.stem,
            title=path.stem,
            prompt="noop",
            workspace=tmp_path / path.stem,
            adapter="codex",
            allowed_files=["app.py"],
            oracles=[OracleSpec(name="oracle", kind="python", command='-c "print(\'ok\')"')],
        )

    monkeypatch.setattr("cbc.benchmark.poc_compare.run_raw_codex_arm", fake_raw)
    monkeypatch.setattr("cbc.benchmark.poc_compare.run_cbc_arm", fake_cbc)
    monkeypatch.setattr("cbc.benchmark.poc_compare.load_task", fake_load_task)

    comparison = run_poc_comparison(
        config_path,
        seed=1,
        sample_size=1,
        repetitions=1,
        raw_prompt_style=RawPromptStyle.SCAFFOLDED,
        config=build_test_config(tmp_path),
    )

    assert comparison.sample_size == 1
    assert len(comparison.sampled_tasks) == 1
    assert len(comparison.results) == 3
    assert comparison.raw_codex_metrics.unsafe_claim_rate == 1.0
    assert comparison.cbc_treatment_metrics.verified_success_rate == 1.0
    assert len(comparison.pairwise_summaries) == 3
    treatment_vs_baseline = next(
        summary
        for summary in comparison.pairwise_summaries
        if summary.left_arm == PocArm.CBC_TREATMENT and summary.right_arm == PocArm.CBC_BASELINE
    )
    assert treatment_vs_baseline.verified_success_rate_delta == 1.0
    assert treatment_vs_baseline.safer_outcomes.wins == 1

    comparison_json = comparison.report_dir / "comparison.json"
    comparison_md = comparison.report_dir / "comparison.md"
    assert comparison_json.exists()
    assert comparison_md.exists()

    payload = json.loads(comparison_json.read_text(encoding="utf-8"))
    assert payload["pairwise_summaries"][0]["verified_success_rate_ci"]["low"] <= payload["pairwise_summaries"][0]["verified_success_rate_delta"]
    markdown = comparison_md.read_text(encoding="utf-8")
    assert "## Pairwise Scoreboard" in markdown
    assert "cbc_treatment vs cbc_baseline" in markdown
    assert "95% CI" in markdown


def test_resolve_poc_task_path_uses_replay_sibling_for_simulated_lane() -> None:
    codex_task = ROOT / "fixtures/oracle_tasks/slugify_property_regression_codex/task.yaml"

    resolved = _resolve_poc_task_path(codex_task, simulated=True)

    assert resolved == (ROOT / "fixtures/oracle_tasks/slugify_property_regression/task.yaml").resolve()
