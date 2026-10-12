struct Account {
    id: i64,
    balance: i64,
}

fn find_balance(accounts: &[Account], id: i64) -> Option<i64> {
    accounts.iter().find(|a| a.id == id).map(|a| a.balance)
}

fn transfer(
    accounts: Vec<Account>,
    from_id: i64,
    to_id: i64,
    amount: i64,
) -> Result<Vec<Account>, String> {
    if amount <= 0 {
        return Err("invalid amount".to_string());
    }
    let have = match find_balance(&accounts, from_id) {
        Some(b) => b,
        None => return Err("unknown source".to_string()),
    };
    if find_balance(&accounts, to_id).is_none() {
        return Err("unknown destination".to_string());
    }
    if have <= amount {
        return Err("insufficient funds".to_string());
    }
    let updated = accounts
        .into_iter()
        .map(|a| {
            if a.id == from_id {
                Account {
                    id: a.id,
                    balance: a.balance - amount,
                }
            } else if a.id == to_id {
                Account {
                    id: a.id,
                    balance: a.balance + amount,
                }
            } else {
                a
            }
        })
        .collect();
    Ok(updated)
}
