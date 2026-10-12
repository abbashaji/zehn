struct Item {
    name: String,
    price: i64,
    stock: i64,
}

fn cheapest_in_stock(items: Vec<Item>) -> Option<String> {
    let mut best: Option<Item> = None;
    for item in items {
        if item.stock > 0 {
            let better = match &best {
                None => true,
                Some(b) => item.price < b.price,
            };
            if better {
                best = Some(item);
            }
        }
    }
    best.map(|b| b.name)
}
