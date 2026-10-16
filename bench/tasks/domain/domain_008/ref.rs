struct Loan {
    item: String,
    due_day: i64,
    renewals: i64,
}

fn renew_loan(loan: Loan, today: i64) -> Result<Loan, String> {
    if today > loan.due_day {
        return Err(format!("overdue by {} days", today - loan.due_day));
    }
    if loan.renewals >= 2 {
        return Err(format!("renewal limit reached for {}", loan.item));
    }
    if today < loan.due_day - 3 {
        return Err(format!("too early: renew from day {}", loan.due_day - 3));
    }
    Ok(Loan {
        item: loan.item,
        due_day: loan.due_day + 14,
        renewals: loan.renewals + 1,
    })
}
