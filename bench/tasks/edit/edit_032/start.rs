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
    ordered.sort_by_key(|p| std::cmp::Reverse(p.score));
    ordered
        .iter()
        .enumerate()
        .map(|(i, p)| Ranked {
            id: p.id,
            rank: i as i64 + 1,
        })
        .collect()
}
