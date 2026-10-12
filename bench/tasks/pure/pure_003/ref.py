from __future__ import annotations

from typing import List


def streak_lengths(readings: List[int]) -> List[int]:
    lengths: List[int] = []
    for i, x in enumerate(readings):
        if i > 0 and x == readings[i - 1]:
            lengths[-1] += 1
        else:
            lengths.append(1)
    return lengths
