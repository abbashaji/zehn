from __future__ import annotations

from bench_prelude import Err, Ok, Result

FREE_MINUTES = 15
BLOCK_MINUTES = 1440
HOUR_RATE = 300
BLOCK_CAP = 1500


def parking_fee(entry: int, exit: int) -> Result[int]:
    if entry < 0:
        return Err("invalid entry time")
    if exit < entry:
        return Err("exit before entry")
    remaining = exit - entry
    grace = FREE_MINUTES
    fee = 0
    while remaining > 0:
        block = min(remaining, BLOCK_MINUTES)
        billable = max(0, block - grace)
        fee += min(BLOCK_CAP, (billable + 59) // 60 * HOUR_RATE)
        grace = 0
        remaining -= block
    return Ok(fee)
