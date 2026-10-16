from __future__ import annotations

from typing import List, Optional


def first_index(xs: List[int], target: int) -> Optional[int]:
    lo = 0
    hi = len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(xs) and xs[lo] == target:
        return lo
    return None
