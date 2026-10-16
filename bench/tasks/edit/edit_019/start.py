from __future__ import annotations

from typing import List

from bench_prelude import Ok, Result


def moving_sum(values: List[int], window: int) -> Result[List[int]]:
    sums: List[int] = []
    total = 0
    for v in values:
        total += v
        sums.append(total)
    return Ok(sums)
