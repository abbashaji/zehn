from __future__ import annotations

from bench_prelude import Err, Ok, Result


def shipping_fee(grams: int) -> Result[int]:
    if grams < 1:
        return Err("invalid weight")
    if grams <= 1000:
        return Ok(500)
    if grams <= 5000:
        return Ok(900)
    return Ok(1500)
