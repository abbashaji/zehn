from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Loan:
    kind: str
    days_late: int


def daily_rate(kind: str) -> Optional[int]:
    if kind == "book":
        return 10
    if kind == "dvd":
        return 50
    if kind == "game":
        return 100
    return None


def total_fine(loans: List[Loan], member: bool) -> Result[int]:
    total = 0
    for loan in loans:
        rate = daily_rate(loan.kind)
        if rate is None:
            return Err("unknown kind")
        if loan.days_late < 0:
            return Err("invalid days")
        days = loan.days_late
        if member:
            days = max(0, days - 3)
        total += min(days * rate, 1500)
    return Ok(min(total, 4000))
