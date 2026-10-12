from __future__ import annotations

from bench_prelude import Err, Ok, Result


def reduce_steps(n: int, cap: int) -> Result[int]:
    if n < 1:
        return Err("start must be positive")
    size = n
    taken = 0
    while size != 1:
        if taken >= cap:
            return Err("step limit exceeded")
        size = size // 3 if size % 3 == 0 else size + 1
        taken += 1
    return Ok(taken)
