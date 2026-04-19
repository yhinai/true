from pricing import compute_total


def checkout_total(subtotal: int, tax_rate: float) -> int:
    return compute_total(subtotal)
