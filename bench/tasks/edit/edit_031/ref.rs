struct Match {
    home: String,
    away: String,
    home_pts: i64,
    away_pts: i64,
    home_tries: i64,
    away_tries: i64,
}

fn match_points(own: i64, other: i64, own_tries: i64) -> i64 {
    let mut points = 0;
    if own > other {
        points = 4;
    } else if own == other {
        points = 2;
    } else if other - own <= 7 {
        points = 1;
    }
    if own_tries >= 4 {
        points += 1;
    }
    points
}

fn league_points(matches: Vec<Match>, team: String) -> Result<i64, String> {
    let mut played = 0;
    let mut total = 0;
    for m in &matches {
        if m.home == team {
            played += 1;
            total += match_points(m.home_pts, m.away_pts, m.home_tries);
        } else if m.away == team {
            played += 1;
            total += match_points(m.away_pts, m.home_pts, m.away_tries);
        }
    }
    if played == 0 {
        return Err("unknown team".to_string());
    }
    Ok(total)
}
