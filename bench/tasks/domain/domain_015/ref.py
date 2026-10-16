from __future__ import annotations

from dataclasses import dataclass

from bench_prelude import Err, Ok, Result


@dataclass
class Summary:
    months: int
    interest: int
    paid: int


def repayment_summary(principal: int, rate_bp: int, payment: int, max_months: int) -> Result[Summary]:
    if principal <= 0:
        return Err("invalid principal")
    if rate_bp < 0:
        return Err("invalid rate")
    if payment <= 0:
        return Err("invalid payment")
    if max_months <= 0:
        return Err("invalid term")
    first = principal * rate_bp // 10000
    if payment <= first:
        return Err("payment too small: interest is %d" % first)
    balance = principal
    total_interest = 0
    total_paid = 0
    for month in range(1, max_months + 1):
        interest = balance * rate_bp // 10000
        owed = balance + interest
        pay = min(payment, owed)
        balance = owed - pay
        total_interest += interest
        total_paid += pay
        if balance == 0:
            return Ok(Summary(month, total_interest, total_paid))
    return Err("not repaid after %d months: %d left" % (max_months, balance))
