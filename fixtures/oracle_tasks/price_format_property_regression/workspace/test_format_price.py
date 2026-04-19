from format_price import format_price


def test_format_price_formats_basic_amount() -> None:
    assert format_price(125) == "$1.25"
