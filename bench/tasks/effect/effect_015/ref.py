from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def check_requests(times: List[int], window: int, limit: int) -> Result[int]:
    if window < 1:
        return Err("window must be positive")
    if limit < 0:
        return Err("limit must not be negative")
    current = -1
    count = 0
    blocked = 0
    for t in times:
        index = t // window
        if index != current:
            current = index
            count = 0
        if count < limit:
            count += 1
            print(f"t={t} allowed ({count}/{limit})")
        else:
            print(f"t={t} blocked")
            blocked += 1
    print(f"blocked: {blocked}")
    return Ok(blocked)
