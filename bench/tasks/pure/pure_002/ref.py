from __future__ import annotations


def next_tick(n: int, step: int) -> int:
    return n - n % step + step
