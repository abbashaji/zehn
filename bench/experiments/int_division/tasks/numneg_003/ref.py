from __future__ import annotations


def floor_mod(a: int, b: int) -> int:
    return a - b * (a // b)
