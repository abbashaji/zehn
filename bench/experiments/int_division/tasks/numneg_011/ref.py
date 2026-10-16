from __future__ import annotations

from typing import List


def trunc_each(xs: List[int], d: int) -> List[int]:
    out = []
    for x in xs:
        q = abs(x) // abs(d)
        out.append(q if (x < 0) == (d < 0) else -q)
    return out
