from __future__ import annotations

from typing import Dict, List


def longest_zero_sum(values: List[int]) -> int:
    firsts: Dict[int, int] = {0: 0}
    total = 0
    best = 0
    for i, x in enumerate(values):
        total += x
        if total in firsts:
            best = max(best, i + 1 - firsts[total])
        else:
            firsts[total] = i + 1
    return best
