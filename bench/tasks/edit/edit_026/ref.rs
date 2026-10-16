fn started_hours(minutes: i64) -> i64 {
    (minutes + 59) / 60
}

fn block_fee(minutes: i64, rate: i64, cap: i64) -> i64 {
    (started_hours(minutes) * rate).min(cap)
}

fn parking_fee(minutes: i64, rate: i64, grace: i64, cap: i64) -> Result<i64, String> {
    if minutes < 0 {
        return Err("invalid duration".to_string());
    }
    if rate < 0 {
        return Err("invalid rate".to_string());
    }
    if grace < 0 || cap < 0 {
        return Err("invalid limit".to_string());
    }
    if minutes <= grace {
        return Ok(0);
    }
    let days = minutes / 1440;
    let rest = minutes % 1440;
    Ok(days * (24 * rate).min(cap) + block_fee(rest, rate, cap))
}
