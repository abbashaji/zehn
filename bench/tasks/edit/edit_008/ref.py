from __future__ import annotations

from typing import Optional


def late_fee(days_late: int, daily: int, cap: Optional[int]) -> int:
    fee = 0 if days_late <= 3 else (days_late - 3) * daily
    if cap is None:
        return fee
    return min(fee, max(cap, 0))
