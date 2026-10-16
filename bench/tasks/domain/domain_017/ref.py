from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from bench_prelude import Err, Ok, Result


@dataclass
class Match:
    home: str
    away: str
    home_goals: int
    away_goals: int


@dataclass
class Row:
    team: str
    played: int
    points: int
    goal_diff: int


def _points(scored: int, conceded: int) -> int:
    if scored > conceded:
        return 3
    if scored == conceded:
        return 1
    return 0


def _add(table: Dict[str, Row], team: str, scored: int, conceded: int) -> None:
    row = table.setdefault(team, Row(team, 0, 0, 0))
    row.played += 1
    row.points += _points(scored, conceded)
    row.goal_diff += scored - conceded


def standings(matches: List[Match]) -> Result[List[Row]]:
    for position, m in enumerate(matches, start=1):
        if m.home == m.away:
            return Err("match %d: a team cannot play itself" % position)
        if m.home_goals < 0 or m.away_goals < 0:
            return Err("match %d: negative goals" % position)
    table: Dict[str, Row] = {}
    for m in matches:
        _add(table, m.home, m.home_goals, m.away_goals)
        _add(table, m.away, m.away_goals, m.home_goals)
    return Ok(sorted(table.values(), key=lambda r: (-r.points, -r.goal_diff)))
