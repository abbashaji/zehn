struct Row {
    name: String,
    qty: i64,
}

fn print_table(rows: Vec<Row>) -> i64 {
    let mut name_w = 4;
    let mut qty_w = 3;
    for row in &rows {
        name_w = name_w.max(row.name.len());
        qty_w = qty_w.max(row.qty.to_string().len());
    }
    println!("{:<name_w$} | {:>qty_w$}", "item", "qty");
    println!("{}-+-{}", "-".repeat(name_w), "-".repeat(qty_w));
    for row in &rows {
        println!("{:<name_w$} | {:>qty_w$}", row.name, row.qty);
    }
    (name_w + 3 + qty_w) as i64
}
