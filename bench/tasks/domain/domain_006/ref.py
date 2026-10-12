from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Stock:
    sku: str
    on_hand: int
    reserved: int


@dataclass
class Order:
    sku: str
    qty: int


def reserve_orders(stock: List[Stock], orders: List[Order]) -> Result[List[Stock]]:
    lines = [Stock(s.sku, s.on_hand, s.reserved) for s in stock]
    for order in orders:
        if order.qty <= 0:
            return Err("invalid quantity for " + order.sku)
        line = next((s for s in lines if s.sku == order.sku), None)
        if line is None:
            return Err("unknown sku: " + order.sku)
        available = line.on_hand - line.reserved
        if available < order.qty:
            return Err("cannot reserve %d of %s: only %d available" % (order.qty, order.sku, available))
        line.reserved += order.qty
    return Ok(lines)
