from __future__ import annotations


def quotient_toward_zero(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q
