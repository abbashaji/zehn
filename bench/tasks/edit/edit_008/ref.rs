fn late_fee(days_late: i64, daily: i64, cap: Option<i64>) -> i64 {
    let fee = if days_late <= 3 {
        0
    } else {
        (days_late - 3) * daily
    };
    match cap {
        None => fee,
        Some(c) => fee.min(c.max(0)),
    }
}
