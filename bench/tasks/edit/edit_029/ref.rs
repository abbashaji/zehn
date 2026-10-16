struct Loan {
    kind: String,
    days_late: i64,
}

fn daily_rate(kind: &str) -> Option<i64> {
    match kind {
        "book" => Some(10),
        "dvd" => Some(50),
        "game" => Some(100),
        _ => None,
    }
}

fn total_fine(loans: Vec<Loan>, member: bool) -> Result<i64, String> {
    let mut total = 0;
    for loan in &loans {
        let rate = match daily_rate(&loan.kind) {
            Some(r) => r,
            None => return Err("unknown kind".to_string()),
        };
        if loan.days_late < 0 {
            return Err("invalid days".to_string());
        }
        let mut days = loan.days_late;
        if member {
            days = (days - 3).max(0);
        }
        total += (days * rate).min(1500);
    }
    Ok(total.min(4000))
}
