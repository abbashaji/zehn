struct Card {
    id: String,
    balance: i64,
    expires: i64,
}

fn pay_bill(cards: Vec<Card>, bill: i64, today: i64) -> Result<Vec<Card>, String> {
    if bill <= 0 {
        return Err("invalid bill".to_string());
    }
    let is_usable = |c: &Card| c.balance > 0 && c.expires >= today;
    let total: i64 = cards
        .iter()
        .filter(|c| is_usable(c))
        .map(|c| c.balance)
        .sum();
    if total < bill {
        return Err(format!("short by {}", bill - total));
    }
    let mut owed = bill;
    let mut used = 0;
    let mut updated = Vec::new();
    for card in cards {
        if owed > 0 && is_usable(&card) {
            let paid = card.balance.min(owed);
            owed -= paid;
            used += 1;
            updated.push(Card {
                id: card.id,
                balance: card.balance - paid,
                expires: card.expires,
            });
        } else {
            updated.push(card);
        }
    }
    if used > 3 {
        return Err(format!("too many cards: needs {}", used));
    }
    Ok(updated)
}
