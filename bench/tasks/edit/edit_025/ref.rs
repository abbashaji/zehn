fn is_leap(year: i64) -> bool {
    if year % 400 == 0 {
        return true;
    }
    if year % 100 == 0 {
        return false;
    }
    year % 4 == 0
}

fn days_in_month(month: i64, year: i64) -> Result<i64, String> {
    if !(1..=12).contains(&month) {
        return Err("invalid month".to_string());
    }
    if year < 1 {
        return Err("invalid year".to_string());
    }
    if month == 2 {
        if is_leap(year) {
            return Ok(29);
        }
        return Ok(28);
    }
    if month == 4 || month == 6 || month == 9 || month == 11 {
        return Ok(30);
    }
    Ok(31)
}
