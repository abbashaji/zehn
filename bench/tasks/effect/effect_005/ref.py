from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def run_ledger(opening: int, moves: List[int]) -> Result[int]:
    if opening < 0:
        return Err("negative opening balance")
    balance = opening
    for n, amount in enumerate(moves, start=1):
        if balance + amount < 0:
            print(f"move {n} rejected: {amount}")
        else:
            balance += amount
            print(f"move {n} ok: balance {balance}")
    print(f"final: {balance}")
    return Ok(balance)
