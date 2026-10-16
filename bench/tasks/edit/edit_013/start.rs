struct Loan {
    id: i64,
    due: i64,
    renewals: i64,
}

fn renew(
    loans: Vec<Loan>,
    id: i64,
    _today: i64,
    _reserved: Vec<i64>,
    _max_renewals: i64,
) -> Result<Vec<Loan>, String> {
    if !loans.iter().any(|l| l.id == id) {
        return Err("unknown loan".to_string());
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
