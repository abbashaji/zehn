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
  let prev_rank = 0;
  ordered.forEach((e, i) => {
    let rank = i + 1;
    if (e.points === 0) {
      rank = 0;
    } else if (e.points === prev_points) {
      rank = prev_rank;
    }
    result.push({ name: e.name, rank });
    prev_points = e.points;
    prev_rank = rank;
  });
  return result;
}
