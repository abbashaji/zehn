from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Item:
    name: str
    price: int
    stock: int


def cheapest_in_stock(items: List[Item]) -> Optional[str]:
    best: Optional[Item] = None
    for item in items:
        if item.stock >= 0 and (best is None or item.price <= best.price):
            best = item
    if best is None:
        return None
    return best.name
