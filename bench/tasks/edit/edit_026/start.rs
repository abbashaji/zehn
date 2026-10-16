fn started_hours(minutes: i64) -> i64 {
    (minutes + 59) / 60
}

fn parking_fee(minutes: i64, rate: i64, _grace: i64, _cap: i64) -> Result<i64, String> {
    if minutes < 0 {
        return Err("invalid duration".to_string());
    }
    if rate < 0 {
        return Err("invalid rate".to_string());
    }
    Ok(started_hours(minutes) * rate)
}
