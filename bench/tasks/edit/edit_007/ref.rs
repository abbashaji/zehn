fn is_leap(year: i64) -> bool {
    if year % 400 == 0 {
        return true;
    }
    if year % 100 == 0 {
        return false;
    }
    year % 4 == 0
}

fn days_in_month(year: i64, month: i64) -> Result<i64, String> {
    if year < 1 {
        return Err("invalid year".to_string());
    }
    if !(1..=12).contains(&month) {
        return Err("invalid month".to_string());
    }
    if month == 2 {
        return Ok(if is_leap(year) { 29 } else { 28 });
    }
    if month == 4 || month == 6 || month == 9 || month == 11 {
        return Ok(30);
    }
    Ok(31)
}
