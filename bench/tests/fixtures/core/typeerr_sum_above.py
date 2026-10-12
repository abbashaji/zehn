from __future__ import annotations

from typing import List


def sum_above(xs: List[int], limit: int) -> int:
    unused: int = "not an int"
    total = 0
    for x in xs:
        if x > limit:
            total += x
    return total
