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
    for b in bookings:
        if begin < b.finish and b.begin < finish:
            return Err("conflict")
    return Ok(bookings + [Booking(begin, finish)])
