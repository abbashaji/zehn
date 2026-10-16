from __future__ import annotations

from bench_prelude import Err, Ok, Result


def started_hours(minutes: int) -> int:
    return (minutes + 59) // 60


def parking_fee(minutes: int, rate: int, grace: int, cap: int) -> Result[int]:
    if minutes < 0:
        return Err("invalid duration")
    if rate < 0:
        return Err("invalid rate")
    return Ok(started_hours(minutes) * rate)
