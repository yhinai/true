from __future__ import annotations

import json
import sys
from contextlib import nullcontext as _nullcontext
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cbc.api.app import create_app
from cbc.api.store import get_benchmark
from cbc.benchmark.local_runner import run_local_benchmark, run_local_controller_benchmark
from cbc.benchmark.poc_compare import RawPromptStyle, run_poc_comparison
from cbc.controller.artifact_flow import render_proof_card
from cbc.controller.orchestrator import review_workspace, run_task
from cbc.intake.dynamic import build_dynamic_task, ensure_dynamic_oracle
from cbc.intake.normalize import load_task
from cbc.models import ControllerBenchmarkComparison, PocMetrics, PocPairwiseSummary, ProofCard
from cbc.review.ci import build_ci_report
from cbc.review.merge_gate import compute_merge_gate
from cbc.review.report import compose_review_report_from_path
from cbc.review.summarize import summarize_run
from cbc.storage.runs import load_recent_runs
from cbc.workspace.backends import SandboxMode

app = typer.Typer(help="Correct by Construction CLI")
console = Console()


@app.command()
def run(
    task_path: Path,
    mode: str = typer.Option("treatment", "--mode", "-m"),
    controller: str = typer.Option("sequential", "--controller"),
    agent: str | None = typer.Option(None, "--agent"),
    json_output: bool = typer.Option(False, "--json"),
    stream: bool = typer.Option(False, "--stream"),
    sandbox: str = typer.Option(
        "local",
        "--sandbox",
        help="Sandbox backend: local (default) or contree",
    ),
) -> None:
    try:
        sandbox_mode = SandboxMode(sandbox)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid sandbox: {sandbox}") from exc
    task = load_task(task_path)
    event_sink = _make_stream_sink() if stream else None
    run_kwargs: dict[str, object] = {
        "mode": mode,
        "controller_mode": controller,
        "sandbox": sandbox_mode,
    }
    if agent is not None:
        run_kwargs["agent_name"] = agent
    if event_sink is not None:
        run_kwargs["event_sink"] = event_sink
    spinner_console = Console(stderr=True)
    show_spinner = (not json_output) and (not stream) and sys.stderr.isatty()
    status_cm = (
        spinner_console.status(
            f"[bold green]Running CBC on {task.task_id}...[/]",
            spinner="dots",
        )
        if show_spinner
        else _nullcontext()
    )
    with status_cm:
        ledger = run_task(task, **run_kwargs)
    if json_output:
        payload = _read_json_artifact(ledger.artifact_dir / "run_artifact.json")
        console.print_json(json.dumps(payload))
        return
    proof_card = ProofCard(
        run_id=ledger.run_id,
        task_id=ledger.task_id,
        mode=ledger.mode,
        verdict=ledger.verdict,
        unsafe_claims=ledger.unsafe_claims,
        attempts=len(ledger.attempts),
        summary=ledger.final_summary,
        proof_points=[f"artifact_dir={ledger.artifact_dir}", f"workspace={ledger.workspace_dir}"],
        artifact_dir=ledger.artifact_dir,
    )
    console.print(render_proof_card(proof_card))
    console.print(f"Artifacts: {ledger.artifact_dir}")


@app.command()
def solve(
    prompt: str = typer.Argument(..., help="What needs to be fixed or built?"),
    verify_cmd: str | None = typer.Option(None, "--verify"),
    controller: str = typer.Option("gearbox", "--controller"),
    agent: str = typer.Option("codex", "--agent"),
    json_output: bool = typer.Option(False, "--json"),
    stream: bool = typer.Option(False, "--stream"),
) -> None:
    task = build_dynamic_task(prompt, Path.cwd(), verify_cmd=verify_cmd, agent_name=agent)
    if not task.oracles:
        task = ensure_dynamic_oracle(task, agent_name=agent)
    event_sink = _make_stream_sink() if stream else None
    if stream:
        ledger = run_task(task, mode="treatment", controller_mode=controller, agent_name=agent, event_sink=event_sink)
    else:
        with console.status("[bold green]Solving with dynamic intake..."):
            ledger = run_task(task, mode="treatment", controller_mode=controller, agent_name=agent)
    if json_output:
        payload = _read_json_artifact(ledger.artifact_dir / "run_artifact.json")
        console.print_json(json.dumps(payload))
        return
    proof_card = ProofCard(
        run_id=ledger.run_id,
        task_id=ledger.task_id,
        mode=ledger.mode,
        verdict=ledger.verdict,
        unsafe_claims=ledger.unsafe_claims,
        attempts=len(ledger.attempts),
        summary=ledger.final_summary,
        proof_points=[f"artifact_dir={ledger.artifact_dir}", f"workspace={ledger.workspace_dir}"],
        artifact_dir=ledger.artifact_dir,
    )
    console.print(render_proof_card(proof_card))
    console.print(f"Artifacts: {ledger.artifact_dir}")


@app.command()
def compare(
    config_path: Path = typer.Option(Path("benchmark-configs/curated_subset.yaml")),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    with console.status("[bold green]Running benchmark comparison..."):
        comparison = run_local_benchmark(config_path)
    if json_output:
        console.print_json(json.dumps(comparison.model_dump(mode="json")))
        return
    table = Table(title="Benchmark")
    table.add_column("Metric")
    table.add_column("Baseline")
    table.add_column("Treatment")
    table.add_row(
        "Verified Success Rate",
        f"{comparison.baseline_metrics.verified_success_rate:.2f}",
        f"{comparison.treatment_metrics.verified_success_rate:.2f}",
    )
    table.add_row(
        "Unsafe Claim Rate",
        f"{comparison.baseline_metrics.unsafe_claim_rate:.2f}",
        f"{comparison.treatment_metrics.unsafe_claim_rate:.2f}",
    )
    console.print(table)
    console.print(f"Reports: {comparison.report_dir}")


@app.command("controller-compare")
def controller_compare(
    config_path: Path = typer.Option(Path("benchmark-configs/controller_subset.yaml")),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    with console.status("[bold green]Running controller comparison..."):
        comparison = run_local_controller_benchmark(config_path)
    if json_output:
        console.print_json(json.dumps(comparison.model_dump(mode="json")))
        return
    _print_controller_comparison(comparison)


@app.command()
def poc(
    config_path: Path = typer.Option(Path("benchmark-configs/poc_live_codex.yaml")),
    seed: int = typer.Option(42),
    sample_size: int = typer.Option(3, min=1),
    repetitions: int = typer.Option(1, min=1),
    raw_prompt_style: RawPromptStyle = typer.Option(RawPromptStyle.SCAFFOLDED),
    simulated: bool = typer.Option(False, "--simulated"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    with console.status("[bold green]Running POC comparison..."):
        comparison = run_poc_comparison(
            config_path,
            seed=seed,
            sample_size=sample_size,
            repetitions=repetitions,
            raw_prompt_style=raw_prompt_style,
            simulated=simulated,
        )
    if json_output:
        console.print_json(json.dumps(comparison.model_dump(mode="json")))
        return
    table = Table(title="POC Comparison")
    table.add_column("Arm")
    table.add_column("Runs")
    table.add_column("Verified Success")
    table.add_column("95% CI")
    table.add_column("Unsafe Claim")
    table.add_column("95% CI")
    table.add_column("Avg Retries")
    table.add_column("Avg Seconds")
    table.add_column("Avg Changed Files")
    for arm, metrics in (
        ("raw_codex", comparison.raw_codex_metrics),
        ("cbc_baseline", comparison.cbc_baseline_metrics),
        ("cbc_treatment", comparison.cbc_treatment_metrics),
    ):
        _add_poc_row(table, arm, metrics)
    console.print(table)
    pairwise_table = Table(title="POC Pairwise Scoreboard")
    pairwise_table.add_column("Comparison")
    pairwise_table.add_column("Pairs")
    pairwise_table.add_column("Success Delta")
    pairwise_table.add_column("95% CI")
    pairwise_table.add_column("Success W-L-T")
    pairwise_table.add_column("Unsafe Reduction")
    pairwise_table.add_column("95% CI")
    pairwise_table.add_column("Safer W-L-T")
    for summary in comparison.pairwise_summaries:
        _add_pairwise_row(pairwise_table, summary)
    console.print(pairwise_table)
    console.print(f"Sampled tasks: {', '.join(path.parent.name for path in comparison.sampled_tasks)}")
    console.print(f"Reports: {comparison.report_dir}")


@app.command()
def review(task_path: Path, mode: str = typer.Option("treatment", "--mode", "-m")) -> None:
    task = load_task(task_path)
    ledger = run_task(task, mode=mode)
    review_report = summarize_run(ledger)
    merge_gate = compute_merge_gate(review_report)
    console.print(f"Review verdict: {review_report.verdict}")
    console.print(review_report.summary)
    console.print(f"Merge gate: {merge_gate.summary}")


@app.command("review-artifact")
def review_artifact(artifact_path: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    report = compose_review_report_from_path(artifact_path)
    if json_output:
        console.print_json(json.dumps(report))
        return
    console.print(f"Review artifact: {report['run_id']}")
    console.print(f"Verification: {report['summary']['verification']['state']}")
    console.print(f"Merge gate: {report['summary']['merge_gate']['verdict']}")
    console.print(f"Risk: {report['summary']['risk']['risk_level']}")


@app.command("review-workspace")
def review_workspace_command(
    task_path: Path,
    workspace_path: Path,
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    task = load_task(task_path)
    ledger = review_workspace(task, workspace_path)
    report = compose_review_report_from_path(ledger.artifact_dir / "run_ledger.json")
    if json_output:
        console.print_json(json.dumps(report))
        return
    console.print(f"Review workspace: {ledger.run_id}")
    console.print(f"Verification: {report['summary']['verification']['state']}")
    console.print(f"Merge gate: {report['summary']['merge_gate']['verdict']}")
    console.print(f"Artifacts: {ledger.artifact_dir}")


@app.command()
def ci(task_path: Path, workspace_path: Path) -> None:
    task = load_task(task_path)
    ledger = review_workspace(task, workspace_path)
    report = compose_review_report_from_path(ledger.artifact_dir / "run_ledger.json")
    ci_report = build_ci_report(report)
    console.print(f"CI verdict: {ci_report['merge_gate_verdict']}")
    console.print(f"Verification: {ci_report['verification_state']}")
    console.print(f"Artifacts: {ledger.artifact_dir}")
    raise typer.Exit(code=int(ci_report["exit_code"]))


@app.command("ci-artifact")
def ci_artifact(artifact_path: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    report = compose_review_report_from_path(artifact_path)
    ci_report = build_ci_report(report)
    if json_output:
        console.print_json(json.dumps(ci_report))
        raise typer.Exit(code=int(ci_report["exit_code"]))
    console.print(f"CI verdict: {ci_report['merge_gate_verdict']}")
    console.print(f"Verification: {ci_report['verification_state']}")
    raise typer.Exit(code=int(ci_report["exit_code"]))


@app.command()
def api(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def trends(last: int = typer.Option(20, "--last", min=1), json_output: bool = typer.Option(False, "--json")) -> None:
    runs = load_recent_runs(Path.cwd() / "artifacts" / "cbc.sqlite3", limit=last)
    if json_output:
        console.print_json(json.dumps(_summarize_trends(runs)))
        return
    table = Table(title=f"Recent Trends ({len(runs)} runs)")
    table.add_column("Run")
    table.add_column("Task")
    table.add_column("Mode")
    table.add_column("Verdict")
    table.add_column("Unsafe")
    table.add_column("Seconds")
    table.add_column("Tokens")
    for run in runs:
        table.add_row(
            str(run["run_id"]),
            str(run["task_id"]),
            str(run["mode"]),
            str(run["verdict"]),
            str(run["unsafe_claims"]),
            f"{float(run['elapsed_seconds']):.2f}",
            str(run["total_tokens"]),
        )
    console.print(table)
    summary = _summarize_trends(runs)
    console.print(
        f"verified_success_rate={summary['verified_success_rate']:.2f} "
        f"unsafe_claim_rate={summary['unsafe_claim_rate']:.2f} "
        f"avg_elapsed_seconds={summary['average_elapsed_seconds']:.2f} "
        f"avg_total_tokens={summary['average_total_tokens']:.2f}"
    )


def _add_poc_row(table: Table, arm: str, metrics: PocMetrics) -> None:
    table.add_row(
        arm,
        str(metrics.total_runs),
        f"{metrics.verified_success_rate:.2f}",
        _format_interval(metrics.verified_success_ci.low, metrics.verified_success_ci.high),
        f"{metrics.unsafe_claim_rate:.2f}",
        _format_interval(metrics.unsafe_claim_ci.low, metrics.unsafe_claim_ci.high),
        f"{metrics.average_retries:.2f}",
        f"{metrics.average_elapsed_seconds:.2f}",
        f"{metrics.average_changed_files:.2f}",
    )


def _add_pairwise_row(table: Table, summary: PocPairwiseSummary) -> None:
    table.add_row(
        f"{summary.left_arm.value} vs {summary.right_arm.value}",
        str(summary.total_pairs),
        f"{summary.verified_success_rate_delta:.2f}",
        _format_interval(summary.verified_success_rate_ci.low, summary.verified_success_rate_ci.high),
        _format_outcomes(
            summary.verified_success_outcomes.wins,
            summary.verified_success_outcomes.losses,
            summary.verified_success_outcomes.ties,
        ),
        f"{summary.unsafe_claim_rate_reduction:.2f}",
        _format_interval(summary.unsafe_claim_rate_reduction_ci.low, summary.unsafe_claim_rate_reduction_ci.high),
        _format_outcomes(
            summary.safer_outcomes.wins,
            summary.safer_outcomes.losses,
            summary.safer_outcomes.ties,
        ),
    )


def _print_controller_comparison(comparison: ControllerBenchmarkComparison) -> None:
    table = Table(title="Controller Benchmark")
    table.add_column("Metric")
    table.add_column("Sequential")
    table.add_column("Gearbox")
    table.add_row(
        "Verified Success Rate",
        f"{comparison.sequential_metrics.verified_success_rate:.2f}",
        f"{comparison.gearbox_metrics.verified_success_rate:.2f}",
    )
    table.add_row(
        "Unsafe Claim Rate",
        f"{comparison.sequential_metrics.unsafe_claim_rate:.2f}",
        f"{comparison.gearbox_metrics.unsafe_claim_rate:.2f}",
    )
    table.add_row(
        "Avg Model Calls",
        f"{comparison.sequential_metrics.average_model_calls:.2f}",
        f"{comparison.gearbox_metrics.average_model_calls:.2f}",
    )
    table.add_row(
        "Avg Total Tokens",
        f"{comparison.sequential_metrics.average_total_tokens:.2f}",
        f"{comparison.gearbox_metrics.average_total_tokens:.2f}",
    )
    console.print(table)
    console.print(f"Recommendation: {comparison.decision.recommended_controller}")
    console.print(comparison.decision.rationale)
    console.print(f"Reports: {comparison.report_dir}")


@app.command("benchmark-artifact")
def benchmark_artifact(benchmark_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    payload = get_benchmark(Path.cwd() / "reports", benchmark_id)
    if payload is None:
        raise typer.Exit(code=1)
    if json_output:
        console.print_json(json.dumps(payload))
        return
    console.print(f"Benchmark artifact: {payload['benchmark_id']}")
    console.print(f"Tasks: {payload.get('task_results') and len(payload['task_results']) or payload.get('total_tasks', 'unknown')}")


def _read_json_artifact(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_stream_sink():
    def sink(event: dict[str, object]) -> None:
        print(json.dumps(event, sort_keys=True), flush=True)

    return sink


def _summarize_trends(runs: list[dict[str, object]]) -> dict[str, float | int]:
    if not runs:
        return {
            "count": 0,
            "verified_success_rate": 0.0,
            "unsafe_claim_rate": 0.0,
            "average_elapsed_seconds": 0.0,
            "average_total_tokens": 0.0,
            "average_estimated_cost_usd": 0.0,
        }
    count = len(runs)
    verified = sum(1 for run in runs if str(run["verdict"]).upper() == "VERIFIED")
    unsafe = sum(1 for run in runs if int(run["unsafe_claims"]) > 0)
    elapsed = sum(float(run["elapsed_seconds"]) for run in runs)
    tokens = sum(int(run["total_tokens"]) for run in runs)
    costs = sum(float(run["estimated_cost_usd"] or 0.0) for run in runs)
    return {
        "count": count,
        "verified_success_rate": verified / count,
        "unsafe_claim_rate": unsafe / count,
        "average_elapsed_seconds": elapsed / count,
        "average_total_tokens": tokens / count,
        "average_estimated_cost_usd": costs / count,
    }


def _format_interval(low: float, high: float) -> str:
    return f"{low:.2f}-{high:.2f}"


def _format_outcomes(wins: int, losses: int, ties: int) -> str:
    return f"{wins}-{losses}-{ties}"


if __name__ == "__main__":
    app()
