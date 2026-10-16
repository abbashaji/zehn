fn merge_unique(a: Vec<i64>, b: Vec<i64>) -> Vec<i64> {
    let mut merged: Vec<i64> = Vec::new();
    let mut i = 0;
    let mut j = 0;
    while i < a.len() && j < b.len() {
        if a[i] < b[j] {
            merged.push(a[i]);
            i += 1;
        } else if a[i] > b[j] {
            merged.push(b[j]);
            j += 1;
        } else {
            merged.push(a[i]);
            merged.push(b[j]);
            i += 1;
            j += 1;
        }
    }
    while j < b.len() {
        merged.push(b[j]);
        j += 1;
    }
    merged
}
