fn merge_unique(a: Vec<i64>, b: Vec<i64>) -> Vec<i64> {
    let mut merged: Vec<i64> = Vec::new();
    let mut i = 0;
    let mut j = 0;
    while i < a.len() || j < b.len() {
        let v = if j >= b.len() || (i < a.len() && a[i] <= b[j]) {
            i += 1;
            a[i - 1]
        } else {
            j += 1;
            b[j - 1]
        };
        if merged.last() != Some(&v) {
            merged.push(v);
        }
    }
    merged
}
