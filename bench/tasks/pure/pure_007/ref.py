from __future__ import annotations

from typing import List, Optional


def second_largest(values: List[int]) -> Optional[int]:
    if not values:
        return None
    top = max(values)
    below = [v for v in values if v < top]
    if not below:
        return None
    return max(below)
