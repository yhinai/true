from demo_repo.checkout.order import Order


def test_order_total_is_preserved() -> None:
    order = Order(order_id="O-1", total=20.0)
    assert order.total == 20.0
