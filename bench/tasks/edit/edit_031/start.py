from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Match:
    home: str
    away: str
    home_pts: int
    away_pts: int
    home_tries: int
    away_tries: int


def match_points(own: int, other: int) -> int:
    if own > other:
        return 4
    if own == other:
        return 2
    return 0


def league_points(matches: List[Match], team: str) -> Result[int]:
    played = 0
    total = 0
    for m in matches:
        if m.home == team:
            played += 1
            total += match_points(m.home_pts, m.away_pts)
        elif m.away == team:
            played += 1
            total += match_points(m.away_pts, m.home_pts)
    if played == 0:
        return Err("unknown team")
    return Ok(total)
