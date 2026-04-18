from pathlib import Path
import os
import sys


EXPECTED = "Hello, verification-first world!\n"


def main() -> int:
    candidate_dir = Path(os.environ["CANDIDATE_DIR"])
    actual = (candidate_dir / "message.txt").read_text(encoding="utf-8")
    if actual != EXPECTED:
        sys.stderr.write(
            "message.txt mismatch.\n"
            f"expected: {EXPECTED!r}\n"
            f"actual:   {actual!r}\n"
        )
        return 1
    sys.stdout.write("Greeting matches expected text.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
