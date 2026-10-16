fn rotate_left(items: Vec<i64>, k: i64) -> Vec<i64> {
    if items.is_empty() {
        return items;
    }
    let mut out = items;
    let shift = (k % out.len() as i64) as usize;
    out.rotate_left(shift);
    out
}
