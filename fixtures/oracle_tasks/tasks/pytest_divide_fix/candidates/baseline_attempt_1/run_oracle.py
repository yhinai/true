import sys

from math_ops import divide


def main() -> int:
    if divide(3, 2) != 1.5:
        return 1
    try:
        divide(1, 0)
    except ZeroDivisionError:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
