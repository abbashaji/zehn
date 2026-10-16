from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Card:
    id: str
    balance: int
    expires: int


def pay_bill(cards: List[Card], bill: int, today: int) -> Result[List[Card]]:
    if bill <= 0:
        return Err("invalid bill")
    total = sum(c.balance for c in cards if c.balance > 0 and c.expires >= today)
    if total < bill:
        return Err("short by %d" % (bill - total))
    owed = bill
    used = 0
    updated: List[Card] = []
    for card in cards:
        if owed > 0 and card.balance > 0 and card.expires >= today:
            paid = min(card.balance, owed)
            owed -= paid
            used += 1
            updated.append(Card(card.id, card.balance - paid, card.expires))
        else:
            updated.append(Card(card.id, card.balance, card.expires))
    if used > 3:
        return Err("too many cards: needs %d" % used)
    return Ok(updated)
