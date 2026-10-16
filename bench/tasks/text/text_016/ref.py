from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def normalize_path(path: str) -> Result[str]:
    stack: List[str] = []
    for segment in path.split("/"):
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if not stack:
                return Err("path escapes root")
            stack.pop()
        else:
            stack.append(segment)
    return Ok("/" + "/".join(stack))
