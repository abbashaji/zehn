from __future__ import annotations

from bench_prelude import Err, Ok, Result


def ticket_price(age: int) -> Result[int]:
    if age < 0:
        return Err("invalid age")
    if age < 5:
        return Ok(0)
    if age < 18:
        return Ok(800)
    if age <= 65:
        return Ok(1500)
    return Ok(1000)
