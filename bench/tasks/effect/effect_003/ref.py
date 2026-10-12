from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Line:
    name: str
    qty: int
    price: int


def print_invoice(lines: List[Line]) -> int:
    total = 0
    for line in lines:
        subtotal = line.qty * line.price
        total += subtotal
        print(f"{line.name} x {line.qty} @ {line.price} = {subtotal}")
    print(f"TOTAL: {total}")
    return total
