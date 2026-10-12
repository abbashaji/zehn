from __future__ import annotations

from typing import List


def join_with(parts: List[str], sep: str) -> str:
    out = ""
    for i, p in enumerate(parts):
        if i > 0:
            out += sep
        out += p
    return out
