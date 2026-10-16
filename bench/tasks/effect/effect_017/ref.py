from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Match:
    home: str
    away: str
    home_goals: int
    away_goals: int


def points_for(mine: int, theirs: int) -> int:
    if mine > theirs:
        return 3
    if mine == theirs:
        return 1
    return 0


def print_results(ms: List[Match]) -> int:
    table: Dict[str, int] = {}
    for m in ms:
        print(f"{m.home} {m.home_goals}-{m.away_goals} {m.away}")
        table[m.home] = table.get(m.home, 0) + points_for(m.home_goals, m.away_goals)
        table[m.away] = table.get(m.away, 0) + points_for(m.away_goals, m.home_goals)
    print("-- table --")
    ranked = sorted(table.items(), key=lambda entry: -entry[1])
    for rank, (team, pts) in enumerate(ranked, start=1):
        print(f"{rank}. {team}: {pts} pts")
    return len(ranked)
