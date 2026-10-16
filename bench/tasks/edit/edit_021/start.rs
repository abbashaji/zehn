fn parking_fee(minutes: i64, rate: i64, _daily_cap: i64) -> Result<i64, String> {
    if minutes < 0 {
        return Err("invalid minutes".to_string());
    }
    if rate < 1 {
        return Err("invalid rate".to_string());
    }
    Ok((minutes + 59) / 60 * rate)
}
