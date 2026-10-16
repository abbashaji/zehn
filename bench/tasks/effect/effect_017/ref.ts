interface Match {
  home: string;
  away: string;
  home_goals: number;
  away_goals: number;
}

function points_for(mine: number, theirs: number): number {
  if (mine > theirs) {
    return 3;
  }
  if (mine === theirs) {
    return 1;
  }
  return 0;
}

function print_results(ms: Match[]): number {
  const table = new Map<string, number>();
  for (const m of ms) {
    console.log(`${m.home} ${m.home_goals}-${m.away_goals} ${m.away}`);
    table.set(m.home, (table.get(m.home) ?? 0) + points_for(m.home_goals, m.away_goals));
    table.set(m.away, (table.get(m.away) ?? 0) + points_for(m.away_goals, m.home_goals));
  }
  console.log("-- table --");
  const ranked = Array.from(table.entries()).sort((a, b) => b[1] - a[1]);
  for (const [i, [team, pts]] of ranked.entries()) {
    console.log(`${i + 1}. ${team}: ${pts} pts`);
  }
  return ranked.length;
}
