from __future__ import annotations

from typing import List


def rotate_left(items: List[int], k: int) -> List[int]:
    if not items:
        return []
    shift = k % len(items)
    return items[shift:] + items[:shift]
