from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Booking:
    begin: int
    finish: int


def add_booking(bookings: List[Booking], begin: int, finish: int, gap: int) -> Result[List[Booking]]:
    if begin >= finish:
        return Err("invalid range")
    if gap < 0:
        return Err("invalid gap")
    for b in bookings:
        if begin < b.finish + gap and b.begin < finish + gap:
            return Err("conflict")
    result: List[Booking] = []
    placed = False
    for b in bookings:
        if not placed and b.begin > begin:
            result.append(Booking(begin, finish))
            placed = True
        result.append(b)
    if not placed:
        result.append(Booking(begin, finish))
    return Ok(result)
