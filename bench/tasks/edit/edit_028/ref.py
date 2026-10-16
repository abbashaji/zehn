from __future__ import annotations

from bench_prelude import Err, Ok, Result


def band_tax(income: int, lower: int, upper: int, percent: int) -> int:
    top = min(income, upper)
    if top <= lower:
        return 0
    return (top - lower) * percent // 100


def income_tax(income: int, children: int) -> Result[int]:
    if income < 0:
        return Err("invalid income")
    if children < 0:
        return Err("invalid children")
    gross = (
        band_tax(income, 10000, 30000, 15)
        + band_tax(income, 30000, 70000, 30)
        + band_tax(income, 70000, income, 45)
    )
    return Ok(max(0, gross - 300 * children))
