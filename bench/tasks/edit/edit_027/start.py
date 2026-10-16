from __future__ import annotations

from typing import List, Optional


def first_index(xs: List[int], target: int) -> Optional[int]:
    lo = 0
    hi = len(xs) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return None
