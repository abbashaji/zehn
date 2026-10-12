from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Seat:
    label: str
    holder: Optional[str]


def book_seat(seats: List[Seat], label: str, guest: str) -> Result[List[Seat]]:
    if guest == "":
        return Err("guest name required")
    target = next((s for s in seats if s.label == label), None)
    if target is None:
        return Err("no such seat: " + label)
    if target.holder is not None:
        return Err("seat already booked: " + label)
    if sum(1 for s in seats if s.holder == guest) >= 2:
        return Err("booking limit reached for " + guest)
    return Ok([Seat(s.label, guest) if s.label == label else s for s in seats])
