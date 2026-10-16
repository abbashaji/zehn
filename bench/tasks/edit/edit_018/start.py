from __future__ import annotations

from typing import List


def compare_versions(a: List[int], b: List[int]) -> int:
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return a[i] - b[i]
    if len(a) < len(b):
        return -1
    if len(a) > len(b):
        return 1
    return 0
