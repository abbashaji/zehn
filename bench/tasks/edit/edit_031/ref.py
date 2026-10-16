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


def match_points(own: int, other: int, own_tries: int) -> int:
    points = 0
    if own > other:
        points = 4
    elif own == other:
        points = 2
    elif other - own <= 7:
        points = 1
    if own_tries >= 4:
        points += 1
    return points


def league_points(matches: List[Match], team: str) -> Result[int]:
    played = 0
    total = 0
    for m in matches:
        if m.home == team:
            played += 1
            total += match_points(m.home_pts, m.away_pts, m.home_tries)
        elif m.away == team:
            played += 1
            total += match_points(m.away_pts, m.home_pts, m.away_tries)
    if played == 0:
        return Err("unknown team")
    return Ok(total)
