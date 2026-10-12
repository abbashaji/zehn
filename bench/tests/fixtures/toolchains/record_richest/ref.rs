struct Account {
    owner: String,
    balance: i64,
    active: bool,
}

fn richest(accts: Vec<Account>) -> Option<Account> {
    let mut best: Option<Account> = None;
    for a in accts {
        let better = match &best {
            Some(b) => a.balance > b.balance,
            None => true,
        };
        if better {
            best = Some(a);
        }
    }
    best
}
