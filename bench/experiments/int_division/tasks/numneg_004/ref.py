from __future__ import annotations

from typing import List


def floor_each(xs: List[int], d: int) -> List[int]:
    return [x // d for x in xs]
