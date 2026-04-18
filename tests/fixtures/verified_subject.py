import icontract
import math


@icontract.require(lambda price: math.isfinite(price) and price >= 0)
@icontract.require(lambda pct: 0 <= pct <= 100)
@icontract.ensure(lambda result: math.isfinite(result) and result >= 0)
def apply_discount(price: float, pct: int) -> float:
    if not math.isfinite(price) or price < 0:
        raise ValueError("price must be a finite non-negative number")
    if not 0 <= pct <= 100:
        raise ValueError("pct must be between 0 and 100")
    return price * (100 - pct) / 100
