from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Player:
    id: int
    score: int


@dataclass
class Ranked:
    id: int
    rank: int


def leaderboard(players: List[Player]) -> List[Ranked]:
    ordered = sorted(players, key=lambda p: (-p.score, p.id))
    return [Ranked(p.id, 1 + sum(1 for q in players if q.score > p.score)) for p in ordered]
