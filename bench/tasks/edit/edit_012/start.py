from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Bracket:
    upto: int
    rate: int


def income_tax(income: int, brackets: List[Bracket], top_rate: int) -> Result[int]:
    if income < 0:
        return Err("invalid income")
    prev = 0
    for b in brackets:
        if b.upto < prev:
            return Err("invalid brackets")
        prev = b.upto
    if top_rate < 0 or top_rate > 100 or any(b.rate < 0 or b.rate > 100 for b in brackets):
        return Err("invalid rate")
    total = 0
    prev = 0
    for b in brackets:
        slice_ = max(0, min(income, b.upto) - prev)
        total += slice_ * b.rate
        prev = b.upto
    if income > prev:
        total += (income - prev) * top_rate
    return Ok(total // 100)
