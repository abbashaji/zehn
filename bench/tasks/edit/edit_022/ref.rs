fn average_without_worst(scores: Vec<i64>) -> Option<i64> {
    if scores.len() < 3 {
        return None;
    }
    let worst = *scores.iter().min()?;
    let mut rest = scores;
    if let Some(pos) = rest.iter().position(|&s| s == worst) {
        rest.remove(pos);
    }
    let n = rest.len() as i64;
    let total: i64 = rest.iter().sum();
    Some((2 * total + n) / (2 * n))
}
