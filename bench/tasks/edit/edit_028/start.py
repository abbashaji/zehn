from __future__ import annotations

from bench_prelude import Err, Ok, Result


def flat_rate(income: int) -> int:
    if income <= 10000:
        return 0
    if income <= 30000:
        return 15
    if income <= 70000:
        return 30
    return 45


def income_tax(income: int, children: int) -> Result[int]:
    if income < 0:
        return Err("invalid income")
    if children < 0:
        return Err("invalid children")
    return Ok(income * flat_rate(income) // 100 - 300 * children)
