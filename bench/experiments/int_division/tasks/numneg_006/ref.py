from __future__ import annotations

from typing import List


def floor_total(xs: List[int], d: int) -> int:
    return sum(x // d for x in xs)
