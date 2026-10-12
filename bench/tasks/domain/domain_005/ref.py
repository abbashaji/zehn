from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result

POINT_CAP = 10000


@dataclass
class Member:
    name: str
    points: int
    tier: str


def _multiplier(tier: str) -> Optional[int]:
    if tier == "bronze":
        return 1
    if tier == "silver":
        return 2
    if tier == "gold":
        return 3
    return None


def _tier_for(points: int) -> str:
    if points < 1000:
        return "bronze"
    if points < 5000:
        return "silver"
    return "gold"


def apply_purchases(m: Member, spends: List[int]) -> Result[Member]:
    if m.points < 0 or m.points > POINT_CAP:
        return Err("invalid member: points out of range")
    if _multiplier(m.tier) is None:
        return Err("unknown tier: " + m.tier)
    current = Member(m.name, m.points, m.tier)
    for i, spend in enumerate(spends):
        if spend < 0:
            return Err("purchase %d: negative spend" % (i + 1))
        factor = _multiplier(current.tier) or 1
        total = min(POINT_CAP, current.points + spend // 10 * factor)
        current = Member(current.name, total, _tier_for(total))
    return Ok(current)
