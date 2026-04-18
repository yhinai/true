from demo_repo.checkout.fulfillment import pair_user_and_order_ids


def test_pair_user_and_order_ids_preserves_both_identities() -> None:
    assert pair_user_and_order_ids("U-1", "O-1") == ("U-1", "O-1")
