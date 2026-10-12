struct Item {
    name: String,
    qty: i64,
}

fn remove_stock(items: Vec<Item>, name: String, qty: i64) -> Result<Vec<Item>, String> {
    if qty <= 0 {
        return Err("quantity must be positive".to_string());
    }
    let have = match items.iter().find(|it| it.name == name) {
        Some(it) => it.qty,
        None => return Err(format!("unknown item: {}", name)),
    };
    if have < qty {
        return Err(format!(
            "insufficient stock for {}: have {}, need {}",
            name, have, qty
        ));
    }
    let updated = items
        .into_iter()
        .map(|it| {
            if it.name == name {
                Item {
                    name: it.name,
                    qty: it.qty - qty,
                }
            } else {
                it
            }
        })
        .collect();
    Ok(updated)
}
