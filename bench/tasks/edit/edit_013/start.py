from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Loan:
    id: int
    due: int
    renewals: int


def find_loan(loans: List[Loan], loan_id: int) -> Optional[Loan]:
    for loan in loans:
        if loan.id == loan_id:
            return loan
    return None


def renew(loans: List[Loan], id: int, today: int, reserved: List[int], max_renewals: int) -> Result[List[Loan]]:
    loan = find_loan(loans, id)
    if loan is None:
        return Err("unknown loan")
    return Ok([Loan(x.id, x.due + 14, x.renewals + 1) if x.id == id else x for x in loans])
