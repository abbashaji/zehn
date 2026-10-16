from __future__ import annotations

from typing import List


def max_drawdown(prices: List[int]) -> int:
    if not prices:
        return 0
    peak = prices[0]
    worst = 0
    for p in prices[1:]:
        worst = max(worst, peak - p)
        peak = max(peak, p)
    return worst
