from __future__ import annotations

from typing import List


def sign_changes(values: List[int]) -> int:
    changes = 0
    prev = 0
    for x in values:
        if x == 0:
            continue
        sign = 1 if x > 0 else -1
        if prev != 0 and sign != prev:
            changes += 1
        prev = sign
    return changes
