from __future__ import annotations

from bench_prelude import Err, Ok, Result


def days_in_month(year: int, month: int) -> Result[int]:
    if month < 1 or month > 12:
        return Err("invalid month")
    if month == 2:
        return Ok(28)
    if month in (4, 6, 9, 11):
        return Ok(30)
    return Ok(31)
