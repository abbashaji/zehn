fn late_fee(days_late: i64, daily: i64, _cap: Option<i64>) -> i64 {
    if days_late <= 3 {
        return 0;
    }
    (days_late - 3) * daily
}
