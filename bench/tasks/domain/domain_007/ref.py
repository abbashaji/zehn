from __future__ import annotations

from typing import Dict, Tuple

from bench_prelude import Err, Ok, Result

RATES: Dict[str, Tuple[int, int, int]] = {
    "local": (300, 50, 30000),
    "national": (500, 100, 30000),
    "international": (1500, 400, 20000),
}


def parcel_fee(zone: str, grams: int) -> Result[int]:
    if grams <= 0:
        return Err("invalid weight")
    if zone not in RATES:
        return Err("unknown zone: " + zone)
    base, extra, limit = RATES[zone]
    if grams > limit:
        return Err("too heavy for %s: limit is %d g" % (zone, limit))
    kilos = (grams + 999) // 1000
    return Ok(base + (kilos - 1) * extra)
