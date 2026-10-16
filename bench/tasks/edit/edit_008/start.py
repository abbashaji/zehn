from __future__ import annotations

from typing import Optional


def late_fee(days_late: int, daily: int, cap: Optional[int]) -> int:
    if days_late <= 3:
        return 0
    return (days_late - 3) * daily
