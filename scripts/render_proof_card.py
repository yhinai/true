from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"Run {payload['run_id']} -> {payload['verdict']}")
    print(f"Task: {payload['task_id']}")
    print(f"Mode: {payload['mode']}")
    print(f"Unsafe claims: {payload['unsafe_claims']}")


if __name__ == "__main__":
    main()
