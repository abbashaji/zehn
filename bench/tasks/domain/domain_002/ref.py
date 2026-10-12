from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Item:
    name: str
    qty: int


def remove_stock(items: List[Item], name: str, qty: int) -> Result[List[Item]]:
    if qty <= 0:
        return Err("quantity must be positive")
    for item in items:
        if item.name == name:
            if item.qty < qty:
                return Err("insufficient stock for %s: have %d, need %d" % (name, item.qty, qty))
            return Ok([Item(it.name, it.qty - qty) if it.name == name else it for it in items])
    return Err("unknown item: " + name)
