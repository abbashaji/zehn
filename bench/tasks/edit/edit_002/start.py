from __future__ import annotations

from typing import List, Optional


def cart_total(prices: List[int], coupon: Optional[int]) -> int:
    return sum(prices)
