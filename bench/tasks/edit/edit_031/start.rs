struct Match {
    home: String,
    away: String,
    home_pts: i64,
    away_pts: i64,
    home_tries: i64,
    away_tries: i64,
}

fn match_points(own: i64, other: i64) -> i64 {
    if own > other {
        return 4;
    }
    if own == other {
        return 2;
    }
    0
}

fn league_points(matches: Vec<Match>, team: String) -> Result<i64, String> {
    let mut played = 0;
    let mut total = 0;
    for m in &matches {
        if m.home == team {
            played += 1;
            total += match_points(m.home_pts, m.away_pts);
        } else if m.away == team {
            played += 1;
            total += match_points(m.away_pts, m.home_pts);
        }
    }
    if played == 0 {
        return Err("unknown team".to_string());
    }
    Ok(total)
}
