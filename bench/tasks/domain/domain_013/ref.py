from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Slot:
    denom: int
    count: int


def make_change(drawer: List[Slot], amount: int) -> Result[List[Slot]]:
    if any(s.denom <= 0 or s.count < 0 for s in drawer):
        return Err("invalid drawer")
    if amount <= 0:
        return Err("invalid amount")
    owed = amount
    updated: List[Slot] = []
    for slot in drawer:
        taken = min(slot.count, owed // slot.denom)
        owed -= taken * slot.denom
        updated.append(Slot(slot.denom, slot.count - taken))
    if owed > 0:
        return Err("cannot make change: %d short" % owed)
    return Ok(updated)
