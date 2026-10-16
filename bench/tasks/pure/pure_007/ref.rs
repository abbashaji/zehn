fn second_largest(values: Vec<i64>) -> Option<i64> {
    let top = values.iter().copied().max()?;
    values.iter().copied().filter(|&v| v < top).max()
}
