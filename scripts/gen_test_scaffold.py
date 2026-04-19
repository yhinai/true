"""Generate a starter test file for a new module.

Usage:
    python3 scripts/gen_test_scaffold.py src/cbc/new_module/foo.py

Writes tests/<mirror>/test_foo.py with a minimal importable-module assertion.
Idempotent: does nothing if the test file already exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def target_test_path(src_path: Path) -> Path:
    rel = src_path.relative_to(REPO_ROOT / "src" / "cbc")
    test_dir = REPO_ROOT / "tests" / rel.parent
    return test_dir / f"test_{src_path.stem}.py"


def scaffold(src_path: Path) -> str:
    module = ".".join(src_path.relative_to(REPO_ROOT / "src").with_suffix("").parts)
    return f'''"""Auto-generated scaffold for {module}."""

from __future__ import annotations


def test_module_imports() -> None:
    import importlib

    mod = importlib.import_module("{module}")
    assert mod is not None
'''


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: gen_test_scaffold.py <src-path>", file=sys.stderr)
        return 2
    src = (REPO_ROOT / sys.argv[1]).resolve()
    if not src.exists() or src.suffix != ".py":
        print(f"not a .py file: {src}", file=sys.stderr)
        return 2
    test_path = target_test_path(src)
    if test_path.exists():
        print(f"exists: {test_path}")
        return 0
    test_path.parent.mkdir(parents=True, exist_ok=True)
    (test_path.parent / "__init__.py").touch(exist_ok=True)
    test_path.write_text(scaffold(src))
    print(f"wrote: {test_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
