#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_report(compare: dict) -> str:
    baseline = compare["baseline"]
    treatment = compare["treatment"]
    policy_lines = [
        "| Setting | Baseline | Treatment |",
        "| --- | --- | --- |",
        f"| max_attempts | {baseline['policy']['max_attempts']} | {treatment['policy']['max_attempts']} |",
        f"| retry_with_evidence | {baseline['policy']['retry_with_evidence']} | {treatment['policy']['retry_with_evidence']} |",
        f"| require_proof_card | {baseline['policy']['require_proof_card']} | {treatment['policy']['require_proof_card']} |",
    ]
    return "\n".join(
        [
            "# Scaffold Compare Report",
            "",
            compare["note"],
            "",
            "## Readiness",
            "",
            f"- Same task set: `{compare['same_task_set']}`",
            f"- Baseline verified success rate: `{baseline['verified_success_rate']:.2f}`",
            f"- Treatment verified success rate: `{treatment['verified_success_rate']:.2f}`",
            f"- Success-rate delta: `{compare['verified_success_rate_delta']:.2f}`",
            "",
            "## Policy Delta",
            "",
            *policy_lines,
            "",
        ]
    ).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two suite-summary.json files.")
    parser.add_argument("--baseline", required=True, help="Path to baseline suite-summary.json")
    parser.add_argument("--treatment", required=True, help="Path to treatment suite-summary.json")
    parser.add_argument("--json-output", required=True, help="Where to write compare.json")
    parser.add_argument("--markdown-output", required=True, help="Where to write compare.md")
    args = parser.parse_args()

    baseline = load_json(Path(args.baseline).resolve())
    treatment = load_json(Path(args.treatment).resolve())

    baseline_task_ids = [task["task_id"] for task in baseline["tasks"]]
    treatment_task_ids = [task["task_id"] for task in treatment["tasks"]]
    compare = {
        "baseline": {
            "suite": baseline["suite"],
            "verified_success_rate": baseline["verified_success_rate"],
            "candidate_source": baseline["candidate_source"],
            "policy": baseline["policy"],
        },
        "treatment": {
            "suite": treatment["suite"],
            "verified_success_rate": treatment["verified_success_rate"],
            "candidate_source": treatment["candidate_source"],
            "policy": treatment["policy"],
        },
        "same_task_set": baseline_task_ids == treatment_task_ids,
        "task_ids": baseline_task_ids,
        "verified_success_rate_delta": treatment["verified_success_rate"] - baseline["verified_success_rate"],
        "note": (
            "This compare report only checks scaffold readiness on the checked-in reference solutions. "
            "It is not an agent-performance benchmark yet."
        ),
    }

    json_output = Path(args.json_output).resolve()
    markdown_output = Path(args.markdown_output).resolve()
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    json_output.write_text(json.dumps(compare, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_output.write_text(markdown_report(compare), encoding="utf-8")
    print(str(json_output))
    print(str(markdown_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
