use std::cmp::{Ordering, Reverse};

struct Match {
    home: String,
    away: String,
    home_goals: i64,
    away_goals: i64,
}

fn points_for(mine: i64, theirs: i64) -> i64 {
    match mine.cmp(&theirs) {
        Ordering::Greater => 3,
        Ordering::Equal => 1,
        Ordering::Less => 0,
    }
}

fn add_points(table: &mut Vec<(String, i64)>, team: &str, pts: i64) {
    match table.iter_mut().find(|entry| entry.0 == team) {
        Some(entry) => entry.1 += pts,
        None => table.push((String::from(team), pts)),
    }
}

fn print_results(ms: Vec<Match>) -> i64 {
    let mut table: Vec<(String, i64)> = Vec::new();
    for m in &ms {
        println!("{} {}-{} {}", m.home, m.home_goals, m.away_goals, m.away);
        add_points(&mut table, &m.home, points_for(m.home_goals, m.away_goals));
        add_points(&mut table, &m.away, points_for(m.away_goals, m.home_goals));
    }
    println!("-- table --");
    table.sort_by_key(|entry| Reverse(entry.1));
    for (i, (team, pts)) in table.iter().enumerate() {
        println!("{}. {}: {} pts", i + 1, team, pts);
    }
    table.len() as i64
}
