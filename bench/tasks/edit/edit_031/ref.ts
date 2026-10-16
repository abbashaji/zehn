type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Match {
  home: string;
  away: string;
  home_pts: number;
  away_pts: number;
  home_tries: number;
  away_tries: number;
}

function match_points(own: number, other: number, own_tries: number): number {
  let points = 0;
  if (own > other) {
    points = 4;
  } else if (own === other) {
    points = 2;
  } else if (other - own <= 7) {
    points = 1;
  }
  if (own_tries >= 4) {
    points += 1;
  }
  return points;
}

function league_points(matches: Match[], team: string): Result<number> {
  let played = 0;
  let total = 0;
  for (const m of matches) {
    if (m.home === team) {
      played += 1;
      total += match_points(m.home_pts, m.away_pts, m.home_tries);
    } else if (m.away === team) {
      played += 1;
      total += match_points(m.away_pts, m.home_pts, m.away_tries);
    }
  }
  if (played === 0) {
    return { ok: false, error: "unknown team" };
  }
  return { ok: true, value: total };
}
