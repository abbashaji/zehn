from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def tariff_bill(limits: List[int], rates: List[int], usage: int) -> Result[int]:
    if len(limits) != len(rates):
        return Err("length mismatch")
    if not limits:
        return Err("no tiers")
    prev = 0
    for limit in limits:
        if limit <= prev:
            return Err("bad limits")
        prev = limit
    if any(r < 0 for r in rates):
        return Err("bad rate")
    if usage < 0:
        return Err("negative usage")
    if usage > limits[-1]:
        return Err("usage above last tier")
    total = 0
    prev = 0
    for limit, rate in zip(limits, rates):
        total += max(0, min(usage, limit) - prev) * rate
        prev = limit
    return Ok(total)
