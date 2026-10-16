from __future__ import annotations


def divmod_toward_zero(a: int, b: int) -> str:
    q = abs(a) // abs(b)
    q = q if (a < 0) == (b < 0) else -q
    return str(q) + " " + str(a - b * q)
