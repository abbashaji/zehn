fn first_index(xs: Vec<i64>, target: i64) -> Option<i64> {
    let mut lo: i64 = 0;
    let mut hi: i64 = xs.len() as i64 - 1;
    while lo < hi {
        let mid = (lo + hi) / 2;
        let v = xs[mid as usize];
        if v == target {
            return Some(mid);
        }
        if v < target {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    None
}
