from __future__ import annotations

from typing import List, Optional


def second_largest(values: List[int]) -> Optional[int]:
    top: Optional[int] = None
    second: Optional[int] = None
    for v in values:
        if top is None or v > top:
            if top is not None:
                second = top
            top = v
        elif v < top and (second is None or v > second):
            second = v
    return second
