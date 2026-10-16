fn parking_fee(minutes: i64, rate: i64, daily_cap: i64) -> Result<i64, String> {
    if minutes < 0 {
        return Err("invalid minutes".to_string());
    }
    if rate < 1 {
        return Err("invalid rate".to_string());
    }
    if daily_cap < 1 {
        return Err("invalid cap".to_string());
    }
    if minutes <= 15 {
        return Ok(0);
    }
    let block_cost = (24 * rate).min(daily_cap);
    let rest = minutes % 1440;
    let partial = ((rest + 59) / 60 * rate).min(daily_cap);
    Ok(minutes / 1440 * block_cost + partial)
}
