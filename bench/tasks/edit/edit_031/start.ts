type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Match {
  home: string;
  away: string;
  home_pts: number;
  away_pts: number;
  home_tries: number;
  away_tries: number;
}

function match_points(own: number, other: number): number {
  if (own > other) {
    return 4;
  }
  if (own === other) {
    return 2;
  }
  return 0;
}

function league_points(matches: Match[], team: string): Result<number> {
  let played = 0;
  let total = 0;
  for (const m of matches) {
    if (m.home === team) {
      played += 1;
      total += match_points(m.home_pts, m.away_pts);
    } else if (m.away === team) {
      played += 1;
      total += match_points(m.away_pts, m.home_pts);
    }
  }
  if (played === 0) {
    return { ok: false, error: "unknown team" };
  }
  return { ok: true, value: total };
}
