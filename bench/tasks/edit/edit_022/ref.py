from __future__ import annotations

from typing import List, Optional


def average_without_worst(scores: List[int]) -> Optional[int]:
    if len(scores) < 3:
        return None
    rest = list(scores)
    rest.remove(min(rest))
    n = len(rest)
    return (2 * sum(rest) + n) // (2 * n)
