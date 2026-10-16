struct Player {
    id: i64,
    score: i64,
}

struct Ranked {
    id: i64,
    rank: i64,
}

fn leaderboard(players: Vec<Player>) -> Vec<Ranked> {
    let mut ordered: Vec<&Player> = players.iter().collect();
    ordered.sort_by(|a, b| b.score.cmp(&a.score).then(a.id.cmp(&b.id)));
    ordered
        .iter()
        .map(|p| Ranked {
            id: p.id,
            rank: 1 + players.iter().filter(|q| q.score > p.score).count() as i64,
        })
        .collect()
}
