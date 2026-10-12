from __future__ import annotations

from typing import List


def weighted_total(points: List[int], weights: List[int]) -> int:
    total = 0
    for p, w in zip(points, weights):
        total += p * w
    return total
