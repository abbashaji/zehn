from __future__ import annotations


def euclid_quotient(a: int, b: int) -> int:
    r = a % abs(b)
    return (a - r) // b
