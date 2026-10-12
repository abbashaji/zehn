from __future__ import annotations

from typing import List


def print_numbered(items: List[str]) -> int:
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item}")
    return len(items)
