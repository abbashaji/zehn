fn print_numbered(items: Vec<String>) -> i64 {
    for (i, item) in items.iter().enumerate() {
        println!("{}. {}", i + 1, item);
    }
    items.len() as i64
}
