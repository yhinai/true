from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    total: float


def build_checkout_state(is_loading: bool, error: str | None) -> tuple[bool, str | None]:
    return is_loading, error
