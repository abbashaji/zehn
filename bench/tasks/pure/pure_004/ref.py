from __future__ import annotations

from typing import List, Optional


def merged_median(a: List[int], b: List[int]) -> Optional[int]:
    total = len(a) + len(b)
    if total == 0:
        return None
    target = (total - 1) // 2
    i = 0
    j = 0
    while True:
        take_a = j >= len(b) or (i < len(a) and a[i] <= b[j])
        value = a[i] if take_a else b[j]
        if i + j == target:
            return value
        if take_a:
            i += 1
        else:
            j += 1
