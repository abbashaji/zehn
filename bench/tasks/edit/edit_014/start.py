from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Entry:
    name: str
    points: int


@dataclass
class Ranked:
    name: str
    rank: int


def rank_players(entries: List[Entry]) -> List[Ranked]:
    ordered = sorted(entries, key=lambda e: -e.points)
    result: List[Ranked] = []
    prev_points = -1
    rank = 0
    for e in ordered:
        if e.points != prev_points:
            rank += 1
        result.append(Ranked(e.name, rank))
        prev_points = e.points
    return result
