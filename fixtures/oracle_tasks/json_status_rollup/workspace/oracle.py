import json
from pathlib import Path
import os
import sys


def main() -> int:
    candidate_dir = Path(os.environ.get("CANDIDATE_DIR", Path.cwd()))
    checks = json.loads((candidate_dir / "checks.json").read_text(encoding="utf-8"))
    summary = json.loads((candidate_dir / "summary.json").read_text(encoding="utf-8"))

    total_checks = len(checks)
    passing_checks = sum(1 for item in checks if item["status"] == "pass")
    failing_checks = sum(1 for item in checks if item["status"] == "fail")
    verified = failing_checks == 0

    expected = {
        "total_checks": total_checks,
        "passing_checks": passing_checks,
        "failing_checks": failing_checks,
        "verified": verified,
    }

    if summary != expected:
        sys.stderr.write(
            "summary.json does not match derived values.\n"
            f"expected: {json.dumps(expected, sort_keys=True)}\n"
            f"actual:   {json.dumps(summary, sort_keys=True)}\n"
        )
        return 1

    sys.stdout.write("summary.json matches derived check counts.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
