fn trimmed_average(scores: Vec<i64>, _drop: i64) -> Option<i64> {
    if scores.is_empty() {
        return None;
    }
    let total: i64 = scores.iter().sum();
    Some(total / scores.len() as i64)
}
