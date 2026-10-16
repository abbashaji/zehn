from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def print_pages(items: List[str], size: int) -> Result[int]:
    if size < 1:
        return Err("page size must be at least 1")
    if not items:
        print("(no items)")
        return Ok(0)
    pages = (len(items) + size - 1) // size
    for page in range(pages):
        print(f"-- page {page + 1} of {pages} --")
        for item in items[page * size : (page + 1) * size]:
            print(item)
    return Ok(pages)
