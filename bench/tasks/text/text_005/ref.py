from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def normalize_headers(line: str) -> Result[str]:
    seen: List[str] = []
    for i, part in enumerate(line.split(",")):
        if part == "":
            return Err("empty header at position " + str(i + 1))
        upper = part.upper()
        if upper in seen:
            return Err("duplicate header: " + upper)
        seen.append(upper)
    return Ok(",".join(seen))
