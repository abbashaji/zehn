struct Stock {
    sku: String,
    on_hand: i64,
    reserved: i64,
}

struct Order {
    sku: String,
    qty: i64,
}

fn reserve_orders(stock: Vec<Stock>, orders: Vec<Order>) -> Result<Vec<Stock>, String> {
    let mut lines = stock;
    for order in orders {
        if order.qty <= 0 {
            return Err(format!("invalid quantity for {}", order.sku));
        }
        let line = match lines.iter_mut().find(|s| s.sku == order.sku) {
            Some(line) => line,
            None => return Err(format!("unknown sku: {}", order.sku)),
        };
        let available = line.on_hand - line.reserved;
        if available < order.qty {
            return Err(format!(
                "cannot reserve {} of {}: only {} available",
                order.qty, order.sku, available
            ));
        }
        line.reserved += order.qty;
    }
    Ok(lines)
}
