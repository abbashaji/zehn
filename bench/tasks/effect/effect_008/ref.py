from __future__ import annotations

from typing import List


def print_head(items: List[str], limit: int) -> int:
    shown = max(0, min(limit, len(items)))
    for item in items[:shown]:
        print(f"- {item}")
    if len(items) > shown:
        print(f"... and {len(items) - shown} more")
    return shown
