struct Account {
    owner: String,
    balance: i64,
    overdraft: i64,
}

fn withdraw(acct: Account, amount: i64) -> Result<Account, String> {
    if amount <= 0 {
        return Err("amount must be positive".to_string());
    }
    if acct.balance - amount < -acct.overdraft {
        return Err("insufficient funds".to_string());
    }
    Ok(Account {
        owner: acct.owner,
        balance: acct.balance - amount,
        overdraft: acct.overdraft,
    })
}
