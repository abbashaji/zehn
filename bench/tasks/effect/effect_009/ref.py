from __future__ import annotations

from typing import List


def scan_alerts(readings: List[int], limit: int) -> int:
    above = False
    started = 0
    for pos, value in enumerate(readings, start=1):
        if value > limit and not above:
            print(f"ALERT {pos}: {value}")
            above = True
            started += 1
        elif value <= limit and above:
            print(f"CLEAR {pos}: {value}")
            above = False
    if above:
        print("still above at end")
    return started
