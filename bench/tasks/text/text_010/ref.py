from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def with_commas(n: int) -> Result[str]:
    if n < 0:
        return Err("negative number: " + str(n))
    digits = str(n)
    groups: List[str] = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return Ok(",".join(groups))
