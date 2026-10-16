use std::cmp::Ordering;

struct Match {
    home: String,
    away: String,
    home_goals: i64,
    away_goals: i64,
}

struct Row {
    team: String,
    played: i64,
    points: i64,
    goal_diff: i64,
}

fn points_for(scored: i64, conceded: i64) -> i64 {
    match scored.cmp(&conceded) {
        Ordering::Greater => 3,
        Ordering::Equal => 1,
        Ordering::Less => 0,
    }
}

fn add_result(table: &mut Vec<Row>, team: &str, scored: i64, conceded: i64) {
    let index = match table.iter().position(|r| r.team == team) {
        Some(i) => i,
        None => {
            table.push(Row {
                team: team.to_string(),
                played: 0,
                points: 0,
                goal_diff: 0,
            });
            table.len() - 1
        }
    };
    let row = &mut table[index];
    row.played += 1;
    row.points += points_for(scored, conceded);
    row.goal_diff += scored - conceded;
}

fn standings(matches: Vec<Match>) -> Result<Vec<Row>, String> {
    for (i, m) in matches.iter().enumerate() {
        if m.home == m.away {
            return Err(format!("match {}: a team cannot play itself", i + 1));
        }
        if m.home_goals < 0 || m.away_goals < 0 {
            return Err(format!("match {}: negative goals", i + 1));
        }
    }
    let mut table: Vec<Row> = Vec::new();
    for m in &matches {
        add_result(&mut table, &m.home, m.home_goals, m.away_goals);
        add_result(&mut table, &m.away, m.away_goals, m.home_goals);
    }
    table.sort_by(|a, b| b.points.cmp(&a.points).then(b.goal_diff.cmp(&a.goal_diff)));
    Ok(table)
}
