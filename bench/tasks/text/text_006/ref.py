from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Item:
    name: str
    qty: int
    cents: int


def money(c: int) -> str:
    rem = c % 100
    pad = "0" + str(rem) if rem < 10 else str(rem)
    return str(c // 100) + "." + pad


def invoice(items: List[Item]) -> Result[str]:
    lines: List[str] = []
    total = 0
    for it in items:
        if it.qty <= 0 or it.cents < 0:
            return Err("invalid item: " + it.name)
        amount = it.qty * it.cents
        total += amount
        lines.append(it.name + " x" + str(it.qty) + " @ " + money(it.cents) + " = " + money(amount))
    lines.append("TOTAL " + money(total))
    return Ok("; ".join(lines))
