from __future__ import annotations

from typing import List, Optional


def cart_total(prices: List[int], coupon: Optional[int]) -> int:
    total = sum(prices)
    if coupon is None:
        return total
    capped = min(max(coupon, 0), 100)
    return total - total * capped // 100
