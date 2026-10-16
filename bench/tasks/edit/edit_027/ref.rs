fn first_index(xs: Vec<i64>, target: i64) -> Option<i64> {
    let mut lo = 0;
    let mut hi = xs.len();
    while lo < hi {
        let mid = (lo + hi) / 2;
        if xs[mid] < target {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if lo < xs.len() && xs[lo] == target {
        return Some(lo as i64);
    }
    None
}
