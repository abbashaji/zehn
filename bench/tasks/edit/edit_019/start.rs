fn moving_sum(values: Vec<i64>, _window: i64) -> Result<Vec<i64>, String> {
    let mut sums: Vec<i64> = Vec::new();
    let mut total = 0;
    for v in values {
        total += v;
        sums.push(total);
    }
    Ok(sums)
}
