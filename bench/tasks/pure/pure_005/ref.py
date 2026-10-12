from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def idle_time(starts: List[int], ends: List[int]) -> Result[int]:
    if len(starts) != len(ends):
        return Err("length mismatch")
    if not starts:
        return Ok(0)
    prev_start = starts[0]
    cover_end = starts[0]
    idle = 0
    for s, e in zip(starts, ends):
        if e < s:
            return Err("bad interval")
        if s < prev_start:
            return Err("unsorted")
        if s > cover_end:
            idle += s - cover_end
        cover_end = max(cover_end, e)
        prev_start = s
    return Ok(idle)
