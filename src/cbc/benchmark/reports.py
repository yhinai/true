from __future__ import annotations

from pathlib import Path

from cbc.models import BenchmarkComparison, ControllerBenchmarkComparison
from cbc.storage.artifacts import write_json, write_markdown

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # pragma: no cover - exercised in CLI smoke runs
    plt = None


def save_benchmark_report(comparison: BenchmarkComparison) -> None:
    comparison.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(comparison.report_dir / "comparison.json", comparison.model_dump(mode="json"))
    write_markdown(comparison.report_dir / "comparison.md", render_benchmark_markdown(comparison))
    render_scoreboard_chart(comparison, comparison.report_dir / "scoreboard.png")


def save_controller_benchmark_report(comparison: ControllerBenchmarkComparison) -> None:
    comparison.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(comparison.report_dir / "comparison.json", comparison.model_dump(mode="json"))
    write_markdown(comparison.report_dir / "comparison.md", render_controller_benchmark_markdown(comparison))


def render_benchmark_markdown(comparison: BenchmarkComparison) -> str:
    return (
        "# Benchmark Comparison\n\n"
        f"- Baseline verified success rate: `{comparison.baseline_metrics.verified_success_rate:.2f}`\n"
        f"- Treatment verified success rate: `{comparison.treatment_metrics.verified_success_rate:.2f}`\n"
        f"- Baseline unsafe claim rate: `{comparison.baseline_metrics.unsafe_claim_rate:.2f}`\n"
        f"- Treatment unsafe claim rate: `{comparison.treatment_metrics.unsafe_claim_rate:.2f}`\n"
        f"- Delta verified success rate: `{comparison.delta_verified_success_rate:.2f}`\n"
        f"- Delta unsafe claim rate: `{comparison.delta_unsafe_claim_rate:.2f}`\n"
    )


def render_controller_benchmark_markdown(comparison: ControllerBenchmarkComparison) -> str:
    return (
        "# Controller Benchmark Comparison\n\n"
        f"- Sequential verified success rate: `{comparison.sequential_metrics.verified_success_rate:.2f}`\n"
        f"- Gearbox verified success rate: `{comparison.gearbox_metrics.verified_success_rate:.2f}`\n"
        f"- Sequential unsafe claim rate: `{comparison.sequential_metrics.unsafe_claim_rate:.2f}`\n"
        f"- Gearbox unsafe claim rate: `{comparison.gearbox_metrics.unsafe_claim_rate:.2f}`\n"
        f"- Sequential average model calls: `{comparison.sequential_metrics.average_model_calls:.2f}`\n"
        f"- Gearbox average model calls: `{comparison.gearbox_metrics.average_model_calls:.2f}`\n"
        f"- Delta verified success rate: `{comparison.delta_verified_success_rate:.2f}`\n"
        f"- Delta unsafe claim rate: `{comparison.delta_unsafe_claim_rate:.2f}`\n"
        f"- Recommended controller: `{comparison.decision.recommended_controller}`\n"
        f"- Promote to default: `{comparison.decision.should_promote_to_default}`\n\n"
        f"## Rationale\n{comparison.decision.rationale}\n"
    )


def render_scoreboard_chart(comparison: BenchmarkComparison, output: Path) -> None:
    if plt is None:
        write_markdown(
            output.with_suffix(".txt"),
            "matplotlib is not installed; scoreboard chart was skipped.\n",
        )
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["Verified Success", "Unsafe Claims"]
    baseline = [
        comparison.baseline_metrics.verified_success_rate,
        comparison.baseline_metrics.unsafe_claim_rate,
    ]
    treatment = [
        comparison.treatment_metrics.verified_success_rate,
        comparison.treatment_metrics.unsafe_claim_rate,
    ]
    x = range(len(labels))
    ax.bar([i - 0.15 for i in x], baseline, width=0.3, label="baseline")
    ax.bar([i + 0.15 for i in x], treatment, width=0.3, label="treatment")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 1)
    ax.legend()
    ax.set_title("Correct by Construction scoreboard")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
