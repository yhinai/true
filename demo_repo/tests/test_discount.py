import pytest

from demo_repo.checkout.discount import apply_discount


def test_apply_discount_rejects_percentages_above_100() -> None:
    with pytest.raises(ValueError):
        apply_discount(100, 150)
