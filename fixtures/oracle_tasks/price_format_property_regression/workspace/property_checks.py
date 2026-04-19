from format_price import format_price


def assert_price_format_properties(value: int) -> None:
    if value < 0:
        return
    result = format_price(value)
    assert result.startswith("$")
    dollars, cents = result[1:].split(".", 1)
    assert dollars.isdigit()
    assert cents.isdigit()
    assert len(cents) == 2
