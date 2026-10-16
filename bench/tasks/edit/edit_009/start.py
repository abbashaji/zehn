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
    value = 0
    count = 0
    for x in readings:
        if count > 0 and x == value and count <= limit:
            count += 1
        else:
            if count > 0:
                runs.append(Run(value, count))
            value = x
            count = 1
    if count > 1:
        runs.append(Run(value, count))
    return Ok(runs)
