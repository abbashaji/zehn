fn print_head(items: Vec<String>, limit: i64) -> i64 {
    let total = items.len() as i64;
    let shown = limit.clamp(0, total);
    for item in items.iter().take(shown as usize) {
        println!("- {}", item);
    }
    if total > shown {
        println!("... and {} more", total - shown);
    }
    shown
}
