fn moving_sum(values: Vec<i64>, window: i64) -> Result<Vec<i64>, String> {
    if window < 1 {
        return Err("invalid window".to_string());
    }
    let mut sums: Vec<i64> = Vec::new();
    for i in 0..values.len() {
        let lo = (i as i64 - window + 1).max(0) as usize;
        sums.push(values[lo..=i].iter().sum());
    }
    Ok(sums)
}
