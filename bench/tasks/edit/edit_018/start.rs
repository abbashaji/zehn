fn compare_versions(a: Vec<i64>, b: Vec<i64>) -> i64 {
    let n = a.len().min(b.len());
    for i in 0..n {
        if a[i] != b[i] {
            return a[i] - b[i];
        }
    }
    if a.len() < b.len() {
        return -1;
    }
    if a.len() > b.len() {
        return 1;
    }
    0
}
