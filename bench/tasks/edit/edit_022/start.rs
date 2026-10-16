fn average_without_worst(scores: Vec<i64>) -> Option<i64> {
    if scores.len() < 2 {
        return None;
    }
    let worst = *scores.iter().min()?;
    let rest: Vec<i64> = scores.into_iter().filter(|&s| s != worst).collect();
    if rest.is_empty() {
        return None;
    }
    let total: i64 = rest.iter().sum();
    Some(total / rest.len() as i64)
}
