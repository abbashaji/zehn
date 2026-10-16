from __future__ import annotations

from typing import List, Optional


def trimmed_average(scores: List[int], drop: int) -> Optional[int]:
    if not scores:
        return None
    return sum(scores) // len(scores)
