import re
import sys

from slugify import slugify


def assert_invariants(sample: str) -> None:
    slug = slugify(sample)
    if slug != slugify(slug):
        raise AssertionError(f"idempotence failed for {sample!r}: {slug!r}")
    if "--" in slug:
        raise AssertionError(f"contains repeated separator for {sample!r}: {slug!r}")
    if slug.startswith("-") or slug.endswith("-"):
        raise AssertionError(f"leading or trailing separator for {sample!r}: {slug!r}")
    if not re.fullmatch(r"[a-z0-9-]*", slug):
        raise AssertionError(f"unexpected characters in {slug!r}")


def main() -> int:
    samples = [
        "Hello  World",
        "already-slugified",
        "A  B  C",
        "trail space ",
        "  lead space",
        "MIXED Case 123",
    ]
    for sample in samples:
        assert_invariants(sample)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
