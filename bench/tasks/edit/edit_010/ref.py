from __future__ import annotations

from typing import List, Optional


def trimmed_average(scores: List[int], drop: int) -> Optional[int]:
    if not scores:
        return None
    k = min(max(drop, 0), len(scores) - 1)
    kept = sorted(scores)[k:]
    return sum(kept) // len(kept)
