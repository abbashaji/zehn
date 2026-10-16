struct Loan {
    id: i64,
    due: i64,
    renewals: i64,
}

fn renew(
    loans: Vec<Loan>,
    id: i64,
    today: i64,
    reserved: Vec<i64>,
    max_renewals: i64,
) -> Result<Vec<Loan>, String> {
    let (due, renewals) = match loans.iter().find(|l| l.id == id) {
        Some(l) => (l.due, l.renewals),
        None => return Err("unknown loan".to_string()),
    };
    if today > due {
        return Err("overdue".to_string());
    }
    if reserved.contains(&id) {
        return Err("reserved".to_string());
    }
    if renewals >= max_renewals {
        return Err("renewal limit".to_string());
    }
    let updated = loans
        .into_iter()
        .map(|l| {
            if l.id == id {
                Loan {
                    id: l.id,
                    due: l.due + 14,
                    renewals: l.renewals + 1,
                }
            } else {
                l
            }
        })
        .collect();
    Ok(updated)
}
