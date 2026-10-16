from __future__ import annotations

from typing import List


def merge_unique(a: List[int], b: List[int]) -> List[int]:
    merged: List[int] = []
    i = 0
    j = 0
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            merged.append(a[i])
            i += 1
        elif a[i] > b[j]:
            merged.append(b[j])
            j += 1
        else:
            merged.append(a[i])
            merged.append(b[j])
            i += 1
            j += 1
    while j < len(b):
        merged.append(b[j])
        j += 1
    return merged
