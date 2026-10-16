fn sign_changes(values: Vec<i64>) -> i64 {
    let mut changes = 0;
    let mut prev = 0;
    for x in values {
        if x == 0 {
            continue;
        }
        let sign = if x > 0 { 1 } else { -1 };
        if prev != 0 && sign != prev {
            changes += 1;
        }
        prev = sign;
    }
    changes
}
