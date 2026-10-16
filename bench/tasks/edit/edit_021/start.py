from __future__ import annotations

from bench_prelude import Err, Ok, Result


def parking_fee(minutes: int, rate: int, daily_cap: int) -> Result[int]:
    if minutes < 0:
        return Err("invalid minutes")
    if rate < 1:
        return Err("invalid rate")
    return Ok((minutes + 59) // 60 * rate)
