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
    ordered = sorted(players, key=lambda p: -p.score)
    return [Ranked(p.id, i + 1) for i, p in enumerate(ordered)]
