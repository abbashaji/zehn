fn merged_median(a: Vec<i64>, b: Vec<i64>) -> Option<i64> {
    let total = a.len() + b.len();
    if total == 0 {
        return None;
    }
    let target = (total - 1) / 2;
    let mut i = 0;
    let mut j = 0;
    loop {
        let take_a = match (a.get(i), b.get(j)) {
            (Some(x), Some(y)) => x <= y,
            (Some(_), None) => true,
            _ => false,
        };
        let value = if take_a { a[i] } else { b[j] };
        if i + j == target {
            return Some(value);
        }
        if take_a {
            i += 1;
        } else {
            j += 1;
        }
    }
}
