from __future__ import annotations

from typing import List, Optional


def average_without_worst(scores: List[int]) -> Optional[int]:
    if len(scores) < 2:
        return None
    worst = min(scores)
    rest = [s for s in scores if s != worst]
    if len(rest) == 0:
        return None
    return sum(rest) // len(rest)
