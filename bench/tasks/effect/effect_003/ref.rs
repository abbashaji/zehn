struct Line {
    name: String,
    qty: i64,
    price: i64,
}

fn print_invoice(lines: Vec<Line>) -> i64 {
    let mut total = 0;
    for line in &lines {
        let subtotal = line.qty * line.price;
        total += subtotal;
        println!(
            "{} x {} @ {} = {}",
            line.name, line.qty, line.price, subtotal
        );
    }
    println!("TOTAL: {}", total);
    total
}
