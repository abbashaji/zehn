fn trimmed_average(scores: Vec<i64>, drop: i64) -> Option<i64> {
    if scores.is_empty() {
        return None;
    }
    let k = drop.max(0).min(scores.len() as i64 - 1) as usize;
    let mut sorted = scores;
    sorted.sort();
    let kept = &sorted[k..];
    let total: i64 = kept.iter().sum();
    Some(total / kept.len() as i64)
}
