struct Shift {
    begin: i64,
    finish: i64,
}

fn merge_shifts(shifts: Vec<Shift>, _gap: i64) -> Result<Vec<Shift>, String> {
    if shifts.iter().any(|s| s.begin >= s.finish) {
        return Err("invalid shift".to_string());
    }
    if shifts.windows(2).any(|w| w[1].begin < w[0].begin) {
        return Err("not sorted".to_string());
    }
    let mut merged: Vec<Shift> = Vec::new();
    for s in shifts {
        if let Some(last) = merged.last_mut() {
            if s.begin < last.finish {
                last.finish = last.finish.max(s.finish);
                continue;
            }
        }
        merged.push(s);
    }
    Ok(merged)
}
