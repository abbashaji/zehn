from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def clean_tags(tags: List[str], limit: int) -> Result[List[str]]:
    if limit < 1:
        return Err("invalid limit")
    cleaned: List[str] = []
    seen: List[str] = []
    for tag in tags:
        key = tag.upper()
        if tag == "" or key in seen:
            continue
        cleaned.append(tag)
        seen.append(key)
    if len(cleaned) > limit:
        return Err("too many tags")
    return Ok(cleaned)
