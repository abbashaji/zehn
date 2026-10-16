from __future__ import annotations


def trunc_remainder(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    q = q if (a < 0) == (b < 0) else -q
    return a - b * q
