from __future__ import annotations

from dataclasses import dataclass

from bench_prelude import Err, Ok, Result


@dataclass
class Loan:
    item: str
    due_day: int
    renewals: int


def renew_loan(loan: Loan, today: int) -> Result[Loan]:
    if today > loan.due_day:
        return Err("overdue by %d days" % (today - loan.due_day))
    if loan.renewals >= 2:
        return Err("renewal limit reached for " + loan.item)
    if today < loan.due_day - 3:
        return Err("too early: renew from day %d" % (loan.due_day - 3))
    return Ok(Loan(loan.item, loan.due_day + 14, loan.renewals + 1))
