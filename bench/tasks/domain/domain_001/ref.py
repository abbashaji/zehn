from __future__ import annotations

from dataclasses import dataclass

from bench_prelude import Err, Ok, Result


@dataclass
class Account:
    owner: str
    balance: int
    overdraft: int


def withdraw(acct: Account, amount: int) -> Result[Account]:
    if amount <= 0:
        return Err("amount must be positive")
    if acct.balance - amount < -acct.overdraft:
        return Err("insufficient funds")
    return Ok(Account(acct.owner, acct.balance - amount, acct.overdraft))
