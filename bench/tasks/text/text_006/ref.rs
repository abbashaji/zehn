struct Item {
    name: String,
    qty: i64,
    cents: i64,
}

fn money(c: i64) -> String {
    format!("{}.{:02}", c / 100, c % 100)
}

fn invoice(items: Vec<Item>) -> Result<String, String> {
    let mut lines: Vec<String> = Vec::new();
    let mut total: i64 = 0;
    for it in &items {
        if it.qty <= 0 || it.cents < 0 {
            return Err(format!("invalid item: {}", it.name));
        }
        let amount = it.qty * it.cents;
        total += amount;
        lines.push(format!(
            "{} x{} @ {} = {}",
            it.name,
            it.qty,
            money(it.cents),
            money(amount)
        ));
    }
    lines.push(format!("TOTAL {}", money(total)));
    Ok(lines.join("; "))
}
