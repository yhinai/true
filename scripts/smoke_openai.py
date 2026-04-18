from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

from axiom.schema import BugClassification, PatchProposal


BUG_A_FUNCTION = """def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
"""

BUG_A_FAILURE = """def test_apply_discount_rejects_percentages_above_100() -> None:
    with pytest.raises(ValueError):
        apply_discount(100, 150)
"""


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set; live OpenAI validation cannot run.", file=sys.stderr)
        return 1

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.4")
    examples_dir = Path("docs/examples")
    examples_dir.mkdir(parents=True, exist_ok=True)

    try:
        classification = client.responses.parse(
            model=model,
            input=(
                "Classify the bug into one Axiom and return structured output.\n\n"
                f"Failing test:\n{BUG_A_FAILURE}\n\n"
                f"Function source:\n{BUG_A_FUNCTION}"
            ),
            text_format=BugClassification,
        ).output_parsed

        patch = client.responses.parse(
            model=model,
            input=(
                "Return a minimal patch for the buggy Python function as structured output.\n"
                "Preserve the function signature.\n\n"
                f"Failing test:\n{BUG_A_FAILURE}\n\n"
                f"Function source:\n{BUG_A_FUNCTION}"
            ),
            text_format=PatchProposal,
        ).output_parsed
    except Exception as exc:
        print(f"OpenAI smoke failed: {exc}", file=sys.stderr)
        return 1

    artifact = {
        "model": model,
        "classification": classification.model_dump(mode="json"),
        "patch": patch.model_dump(mode="json"),
    }
    output_path = examples_dir / "openai_smoke_success.json"
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"Saved structured-output smoke artifact to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
