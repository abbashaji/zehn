struct Summary {
    months: i64,
    interest: i64,
    paid: i64,
}

fn repayment_summary(
    principal: i64,
    rate_bp: i64,
    payment: i64,
    max_months: i64,
) -> Result<Summary, String> {
    if principal <= 0 {
        return Err("invalid principal".to_string());
    }
    if rate_bp < 0 {
        return Err("invalid rate".to_string());
    }
    if payment <= 0 {
        return Err("invalid payment".to_string());
    }
    if max_months <= 0 {
        return Err("invalid term".to_string());
    }
    let first = principal * rate_bp / 10000;
    if payment <= first {
        return Err(format!("payment too small: interest is {}", first));
    }
    let mut balance = principal;
    let mut total_interest = 0;
    let mut total_paid = 0;
    for month in 1..=max_months {
        let interest = balance * rate_bp / 10000;
        let owed = balance + interest;
        let pay = payment.min(owed);
        balance = owed - pay;
        total_interest += interest;
        total_paid += pay;
        if balance == 0 {
            return Ok(Summary {
                months: month,
                interest: total_interest,
                paid: total_paid,
            });
        }
    }
    Err(format!(
        "not repaid after {} months: {} left",
        max_months, balance
    ))
}
