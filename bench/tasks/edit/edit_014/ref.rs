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
    let mut prev_rank = 0;
    for (i, e) in ordered.into_iter().enumerate() {
        let rank = if e.points == 0 {
            0
        } else if e.points == prev_points {
            prev_rank
        } else {
            i as i64 + 1
        };
        prev_points = e.points;
        prev_rank = rank;
        result.push(Ranked { name: e.name, rank });
    }
    result
}
