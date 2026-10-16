from __future__ import annotations

from typing import Dict, List


def schedule_length(tasks: List[int], cooldown: int) -> int:
    last: Dict[int, int] = {}
    now = 0
    for kind in tasks:
        now += 1
        if kind in last:
            now = max(now, last[kind] + cooldown + 1)
        last[kind] = now
    return now
