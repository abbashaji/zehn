use std::cmp::Reverse;

struct Entry {
    name: String,
    points: i64,
}

struct Ranked {
    name: String,
    rank: i64,
}

fn rank_players(entries: Vec<Entry>) -> Vec<Ranked> {
    let mut ordered = entries;
    ordered.sort_by_key(|e| Reverse(e.points));
    let mut result = Vec::new();
    let mut prev_points = -1;
    let mut rank = 0;
    for e in ordered {
        if e.points != prev_points {
            rank += 1;
        }
        prev_points = e.points;
        result.push(Ranked { name: e.name, rank });
    }
    result
}
