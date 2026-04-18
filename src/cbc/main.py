from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cbc.api.app import create_app
from cbc.benchmark.local_runner import run_local_benchmark
from cbc.controller.artifact_flow import render_proof_card
from cbc.controller.orchestrator import run_task
from cbc.intake.normalize import load_task
from cbc.models import ProofCard
from cbc.review.merge_gate import compute_merge_gate
from cbc.review.summarize import summarize_run

app = typer.Typer(help="Correct by Construction CLI")
console = Console()


@app.command()
def run(task_path: Path, mode: str = typer.Option("treatment", "--mode", "-m")) -> None:
    task = load_task(task_path)
    ledger = run_task(task, mode=mode)
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
def compare(config_path: Path = typer.Option(Path("benchmark-configs/curated_subset.yaml"))) -> None:
    comparison = run_local_benchmark(config_path)
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


@app.command()
def review(task_path: Path, mode: str = typer.Option("treatment", "--mode", "-m")) -> None:
    task = load_task(task_path)
    ledger = run_task(task, mode=mode)
    review_report = summarize_run(ledger)
    merge_gate = compute_merge_gate(review_report)
    console.print(f"Review verdict: {review_report.verdict}")
    console.print(review_report.summary)
    console.print(f"Merge gate: {merge_gate.summary}")


@app.command()
def api(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    app()
