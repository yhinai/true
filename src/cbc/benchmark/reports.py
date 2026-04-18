from __future__ import annotations

import json
from pathlib import Path

from .types import BenchmarkComparison, to_builtin


def render_markdown_report(comparison: BenchmarkComparison) -> str:
    baseline = comparison.baseline_metrics
    treatment = comparison.treatment_metrics
    delta = comparison.delta_metrics
    lines = [
        "# Correct by Construction Benchmark Comparison",
        "",
        f"- Run ID: `{comparison.run_id}`",
        f"- Generated: `{comparison.generated_at}`",
        "",
        "## Metrics",
        "",
        "| Metric | Baseline | Treatment | Delta (Treatment - Baseline) |",
        "|---|---:|---:|---:|",
        "| Verified Success Rate | "
        f"{baseline['verified_success_rate']:.4f} | "
        f"{treatment['verified_success_rate']:.4f} | "
        f"{delta['verified_success_rate_delta']:+.4f} |",
        "| Unsafe Claim Rate | "
        f"{baseline['unsafe_claim_rate']:.4f} | "
        f"{treatment['unsafe_claim_rate']:.4f} | "
        f"{delta['unsafe_claim_rate_delta']:+.4f} |",
        "| Mean Duration (s) | "
        f"{baseline['mean_duration_s']:.4f} | "
        f"{treatment['mean_duration_s']:.4f} | "
        f"{delta['mean_duration_s_delta']:+.4f} |",
        "| Mean Retries | "
        f"{baseline['mean_retries']:.4f} | "
        f"{treatment['mean_retries']:.4f} | "
        f"{delta['mean_retries_delta']:+.4f} |",
        "",
        "## Task Outcomes",
        "",
        "| Task ID | Baseline Verified | Treatment Verified | Baseline Unsafe | Treatment Unsafe |",
        "|---|---:|---:|---:|---:|",
    ]

    baseline_by_task = {result.task_id: result for result in comparison.baseline_results}
    treatment_by_task = {result.task_id: result for result in comparison.treatment_results}
    for task_id in sorted(baseline_by_task):
        b = baseline_by_task[task_id]
        t = treatment_by_task[task_id]
        lines.append(
            f"| {task_id} | {int(b.verified)} | {int(t.verified)} | {int(b.unsafe_claim)} | {int(t.unsafe_claim)} |"
        )

    return "\n".join(lines) + "\n"


def write_comparison_json(comparison: BenchmarkComparison, target_path: Path) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(to_builtin(comparison), indent=2), encoding="utf-8")
    return str(target_path.resolve())


def write_markdown_report(comparison: BenchmarkComparison, target_path: Path) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(render_markdown_report(comparison), encoding="utf-8")
    return str(target_path.resolve())

