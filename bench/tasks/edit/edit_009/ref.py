from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Run:
    value: int
    count: int


def compress(readings: List[int], limit: int) -> Result[List[Run]]:
    if limit < 1:
        return Err("invalid limit")
    runs: List[Run] = []
    for x in readings:
        if runs and runs[-1].value == x and runs[-1].count < limit:
            runs[-1].count += 1
        else:
            runs.append(Run(x, 1))
    return Ok(runs)
