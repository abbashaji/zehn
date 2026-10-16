struct Run {
    value: i64,
    count: i64,
}

fn compress(readings: Vec<i64>, limit: i64) -> Result<Vec<Run>, String> {
    if limit < 1 {
        return Err("invalid limit".to_string());
    }
    let mut runs: Vec<Run> = Vec::new();
    let mut value = 0;
    let mut count = 0;
    for x in readings {
        if count > 0 && x == value && count <= limit {
            count += 1;
        } else {
            if count > 0 {
                runs.push(Run { value, count });
            }
            value = x;
            count = 1;
        }
    }
    if count > 1 {
        runs.push(Run { value, count });
    }
    Ok(runs)
}
