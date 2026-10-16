fn days_in_month(_year: i64, month: i64) -> Result<i64, String> {
    if !(1..=12).contains(&month) {
        return Err("invalid month".to_string());
    }
    if month == 2 {
        return Ok(28);
    }
    if month == 4 || month == 6 || month == 9 || month == 11 {
        return Ok(30);
    }
    Ok(31)
}
