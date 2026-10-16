from __future__ import annotations

from bench_prelude import Err, Ok, Result


def parking_fee(minutes: int, rate: int, daily_cap: int) -> Result[int]:
    if minutes < 0:
        return Err("invalid minutes")
    if rate < 1:
        return Err("invalid rate")
    if daily_cap < 1:
        return Err("invalid cap")
    if minutes <= 15:
        return Ok(0)
    block_cost = min(24 * rate, daily_cap)
    rest = minutes % 1440
    partial = min((rest + 59) // 60 * rate, daily_cap)
    return Ok(minutes // 1440 * block_cost + partial)
