from __future__ import annotations

from bench_prelude import Err, Ok, Result

PRICES = {"free": 0, "basic": 900, "pro": 2900, "team": 7900}


def change_plan(current: str, target: str, days_used: int, cycle_days: int) -> Result[int]:
    if current not in PRICES:
        return Err("unknown plan: " + current)
    if target not in PRICES:
        return Err("unknown plan: " + target)
    if cycle_days <= 0 or days_used < 0 or days_used > cycle_days:
        return Err("invalid cycle")
    if current == target:
        return Err("already on plan " + current)
    if target == "team" and current != "pro":
        return Err("team plan requires pro")
    if PRICES[target] < PRICES[current] and days_used > 7:
        return Err("downgrade not allowed after day 7")
    days_left = cycle_days - days_used
    charge = PRICES[target] * days_left // cycle_days
    credit = PRICES[current] * days_left // cycle_days
    return Ok(charge - credit)
