from __future__ import annotations

from bench_prelude import Err, Ok, Result


def is_leap(year: int) -> bool:
    return year % 4 == 0


def days_in_month(year: int, month: int) -> Result[int]:
    if year < 1:
        return Err("invalid year")
    if month < 1 or month > 12:
        return Err("invalid month")
    if month == 2:
        return Ok(29 if is_leap(year) else 28)
    if month in (4, 6, 9, 11):
        return Ok(30)
    return Ok(31)
