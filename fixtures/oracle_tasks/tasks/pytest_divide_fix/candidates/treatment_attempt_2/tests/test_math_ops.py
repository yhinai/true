import pytest

from math_ops import divide


def test_divide_returns_float() -> None:
    assert divide(3, 2) == 1.5


def test_divide_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
