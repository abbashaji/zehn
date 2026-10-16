from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def max_depth(steps: List[int]) -> Result[int]:
    depth = 0
    deepest = 0
    for s in steps:
        if s == 1:
            depth += 1
            deepest = max(deepest, depth)
        elif s == -1:
            if depth == 0:
                return Err("closed too early")
            depth -= 1
        else:
            return Err("bad step")
    if depth > 0:
        return Err("left open")
    return Ok(deepest)
