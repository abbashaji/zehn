from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Employee:
    name: str
    dept: str
    salary: int
    active: bool


def payroll_total(staff: List[Employee], dept: Optional[str]) -> int:
    total = 0
    for e in staff:
        if not e.active:
            continue
        if dept is not None and e.dept.upper() != dept.upper():
            continue
        total += e.salary
    return total
