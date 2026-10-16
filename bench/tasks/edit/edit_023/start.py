from __future__ import annotations

from typing import List

from bench_prelude import Ok, Result


def clean_tags(tags: List[str], limit: int) -> Result[List[str]]:
    kept: List[str] = []
    for tag in tags:
        if tag not in kept:
            kept.append(tag)
    return Ok(kept)
