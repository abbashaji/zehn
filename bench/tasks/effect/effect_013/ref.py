from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Row:
    name: str
    qty: int


def print_table(rows: List[Row]) -> int:
    name_w = max([4] + [len(row.name) for row in rows])
    qty_w = max([3] + [len(str(row.qty)) for row in rows])
    print(f"{'item'.ljust(name_w)} | {'qty'.rjust(qty_w)}")
    print("-" * name_w + "-+-" + "-" * qty_w)
    for row in rows:
        print(f"{row.name.ljust(name_w)} | {str(row.qty).rjust(qty_w)}")
    return name_w + 3 + qty_w
