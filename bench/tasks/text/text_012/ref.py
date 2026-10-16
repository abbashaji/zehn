from __future__ import annotations

from typing import List


def align_column(values: List[int]) -> str:
    width = 0
    for v in values:
        width = max(width, len(str(v)))
    cells = [str(v).rjust(width) for v in values]
    return "|".join(cells)
