from __future__ import annotations

from typing import List


def merge_unique(a: List[int], b: List[int]) -> List[int]:
    merged: List[int] = []
    i = 0
    j = 0
    while i < len(a) or j < len(b):
        if j >= len(b) or (i < len(a) and a[i] <= b[j]):
            v = a[i]
            i += 1
        else:
            v = b[j]
            j += 1
        if not merged or merged[-1] != v:
            merged.append(v)
    return merged
