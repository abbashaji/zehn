from __future__ import annotations


def hour_after(hour: int, delta: int) -> int:
    return (hour + delta) % 24
