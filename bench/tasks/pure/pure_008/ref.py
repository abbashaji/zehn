from __future__ import annotations

from bench_prelude import Err, Ok, Result


def digit_count(n: int, base: int) -> Result[int]:
    if n < 0:
        return Err("negative number")
    if base < 2:
        return Err("base must be at least 2")
    count = 1
    rest = n
    while rest >= base:
        rest //= base
        count += 1
    return Ok(count)
