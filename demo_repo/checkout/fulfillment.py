def mark_fulfilled(order_id: str) -> str:
    return f"{order_id}:fulfilled"


def pair_user_and_order_ids(user_id: str, order_id: str) -> tuple[str, str]:
    return user_id, user_id
