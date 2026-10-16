from __future__ import annotations

from typing import List


def mean_toward_zero(xs: List[int]) -> int:
    if not xs:
        return 0
    total = sum(xs)
    q = abs(total) // len(xs)
    return q if total >= 0 else -q
