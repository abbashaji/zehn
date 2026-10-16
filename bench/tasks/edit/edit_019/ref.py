from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def moving_sum(values: List[int], window: int) -> Result[List[int]]:
    if window < 1:
        return Err("invalid window")
    sums: List[int] = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        sums.append(sum(values[lo : i + 1]))
    return Ok(sums)
