interface Player {
  id: number;
  score: number;
}

interface Ranked {
  id: number;
  rank: number;
}

function leaderboard(players: Player[]): Ranked[] {
  const ordered = [...players].sort((a, b) => b.score - a.score);
  return ordered.map((p, i): Ranked => ({ id: p.id, rank: i + 1 }));
}
