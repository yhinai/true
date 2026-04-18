import icontract


@icontract.ensure(lambda result: result >= 0)
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
