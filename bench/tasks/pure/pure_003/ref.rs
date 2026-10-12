fn streak_lengths(readings: Vec<i64>) -> Vec<i64> {
    let mut lengths: Vec<i64> = Vec::new();
    let mut prev: Option<i64> = None;
    for x in readings {
        match (prev, lengths.last_mut()) {
            (Some(p), Some(last)) if p == x => *last += 1,
            _ => lengths.push(1),
        }
        prev = Some(x);
    }
    lengths
}
