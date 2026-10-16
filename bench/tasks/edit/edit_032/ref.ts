interface Player {
  id: number;
  score: number;
}

interface Ranked {
  id: number;
  rank: number;
}

function leaderboard(players: Player[]): Ranked[] {
  const ordered = [...players].sort((a, b) => (a.score !== b.score ? b.score - a.score : a.id - b.id));
  return ordered.map((p): Ranked => ({
    id: p.id,
    rank: 1 + players.filter((q) => q.score > p.score).length,
  }));
}
