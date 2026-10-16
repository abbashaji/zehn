from __future__ import annotations

from bench_prelude import Err, Ok, Result


def started_hours(minutes: int) -> int:
    return (minutes + 59) // 60


def block_fee(minutes: int, rate: int, cap: int) -> int:
    return min(started_hours(minutes) * rate, cap)


def parking_fee(minutes: int, rate: int, grace: int, cap: int) -> Result[int]:
    if minutes < 0:
        return Err("invalid duration")
    if rate < 0:
        return Err("invalid rate")
    if grace < 0 or cap < 0:
        return Err("invalid limit")
    if minutes <= grace:
        return Ok(0)
    days = minutes // 1440
    rest = minutes % 1440
    return Ok(days * min(24 * rate, cap) + block_fee(rest, rate, cap))
