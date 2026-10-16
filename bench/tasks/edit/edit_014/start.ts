interface Entry {
  name: string;
  points: number;
}

interface Ranked {
  name: string;
  rank: number;
}

function rank_players(entries: Entry[]): Ranked[] {
  const ordered = [...entries].sort((a, b) => b.points - a.points);
  const result: Ranked[] = [];
  let prev_points = -1;
  let rank = 0;
  for (const e of ordered) {
    if (e.points !== prev_points) {
      rank += 1;
    }
    result.push({ name: e.name, rank });
    prev_points = e.points;
  }
  return result;
}
