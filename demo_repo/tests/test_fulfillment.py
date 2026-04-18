from demo_repo.checkout.fulfillment import mark_fulfilled


def test_mark_fulfilled_prefixes_status() -> None:
    assert mark_fulfilled("O-1") == "O-1:fulfilled"
