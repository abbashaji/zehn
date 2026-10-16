from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Shift:
    begin: int
    finish: int


def merge_shifts(shifts: List[Shift], gap: int) -> Result[List[Shift]]:
    if gap < 0:
        return Err("invalid gap")
    if any(s.begin >= s.finish for s in shifts):
        return Err("invalid shift")
    for i in range(1, len(shifts)):
        if shifts[i].begin < shifts[i - 1].begin:
            return Err("not sorted")
    merged: List[Shift] = []
    for s in shifts:
        if merged and s.begin <= merged[-1].finish + gap:
            merged[-1].finish = max(merged[-1].finish, s.finish)
        else:
            merged.append(Shift(s.begin, s.finish))
    return Ok(merged)
