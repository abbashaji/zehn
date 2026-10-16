from __future__ import annotations

from typing import List


def rotate_left(xs: List[int], k: int) -> List[int]:
    if not xs:
        return []
    s = k % len(xs)
    return xs[s:] + xs[:s]
