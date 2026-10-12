from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Account:
    id: int
    balance: int


def find_balance(accounts: List[Account], account_id: int) -> Optional[int]:
    for a in accounts:
        if a.id == account_id:
            return a.balance
    return None


def transfer(accounts: List[Account], from_id: int, to_id: int, amount: int) -> Result[List[Account]]:
    if amount <= 0:
        return Err("invalid amount")
    if from_id == to_id:
        return Err("same account")
    have = find_balance(accounts, from_id)
    if have is None:
        return Err("unknown source")
    if find_balance(accounts, to_id) is None:
        return Err("unknown destination")
    if have < amount:
        return Err("insufficient funds")
    updated: List[Account] = []
    for a in accounts:
        if a.id == from_id:
            updated.append(Account(a.id, a.balance - amount))
        elif a.id == to_id:
            updated.append(Account(a.id, a.balance + amount))
        else:
            updated.append(a)
    return Ok(updated)
