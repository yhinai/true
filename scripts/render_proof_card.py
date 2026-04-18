#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def render(verification: dict) -> str:
    verdict = "PASS" if verification["passed"] else "FAIL"
    allowed_paths = ", ".join(verification["allowed_paths"])
    oracle_command = " ".join(verification["oracle_command"])
    return "\n".join(
        [
            f"# Proof Card: {verification['task_id']}",
            "",
            f"- Verdict: `{verdict}`",
            f"- Suite: `{verification['suite']}`",
            f"- Candidate source: `{verification['candidate_source']}`",
            f"- Oracle kind: `{verification['oracle_kind']}`",
            f"- Oracle command: `{oracle_command}`",
            f"- Allowed paths: `{allowed_paths}`",
            f"- Duration ms: `{verification['duration_ms']}`",
            "",
            "## Prompt",
            "",
            verification["prompt"].rstrip(),
            "",
        ]
    ).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a markdown proof card from a verification report.")
    parser.add_argument("--input", required=True, help="Path to verification.json")
    parser.add_argument("--output", required=True, help="Path to write proof-card markdown")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    verification = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.write_text(render(verification), encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
