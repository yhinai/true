from demo_repo.checkout.order import build_checkout_state


def test_checkout_state_normalizes_loading_when_error_exists() -> None:
    assert build_checkout_state(True, "network failed") == (False, "network failed")
