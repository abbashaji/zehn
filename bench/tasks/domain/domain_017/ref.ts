interface Match {
  home: string;
  away: string;
  home_goals: number;
  away_goals: number;
}

interface Row {
  team: string;
  played: number;
  points: number;
  goal_diff: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function pointsFor(scored: number, conceded: number): number {
  if (scored > conceded) {
    return 3;
  }
  return scored === conceded ? 1 : 0;
}

function addResult(table: Row[], team: string, scored: number, conceded: number): void {
  let row = table.find((r) => r.team === team);
  if (row === undefined) {
    row = { team, played: 0, points: 0, goal_diff: 0 };
    table.push(row);
  }
  row.played += 1;
  row.points += pointsFor(scored, conceded);
  row.goal_diff += scored - conceded;
}

function standings(matches: Match[]): Result<Row[]> {
  let position = 0;
  for (const m of matches) {
    position += 1;
    if (m.home === m.away) {
      return { ok: false, error: "match " + position + ": a team cannot play itself" };
    }
    if (m.home_goals < 0 || m.away_goals < 0) {
      return { ok: false, error: "match " + position + ": negative goals" };
    }
  }
  const table: Row[] = [];
  for (const m of matches) {
    addResult(table, m.home, m.home_goals, m.away_goals);
    addResult(table, m.away, m.away_goals, m.home_goals);
  }
  const ordered = [...table].sort((a, b) => b.points - a.points || b.goal_diff - a.goal_diff);
  return { ok: true, value: ordered };
}
