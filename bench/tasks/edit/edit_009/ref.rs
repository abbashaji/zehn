struct Run {
    value: i64,
    count: i64,
}

fn compress(readings: Vec<i64>, limit: i64) -> Result<Vec<Run>, String> {
    if limit < 1 {
        return Err("invalid limit".to_string());
    }
    let mut runs: Vec<Run> = Vec::new();
    for x in readings {
        if let Some(last) = runs.last_mut() {
            if last.value == x && last.count < limit {
                last.count += 1;
                continue;
            }
        }
        runs.push(Run { value: x, count: 1 });
    }
    Ok(runs)
}
