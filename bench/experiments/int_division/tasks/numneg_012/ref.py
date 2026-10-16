from __future__ import annotations


def whole_steps(offset: int, step: int) -> int:
    q = abs(offset) // step
    return q if offset >= 0 else -q
