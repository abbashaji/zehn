const STATUSES: [&str; 7] = [
    "new",
    "paid",
    "packed",
    "shipped",
    "delivered",
    "cancelled",
    "refunded",
];
const EVENTS: [&str; 6] = ["pay", "pack", "ship", "deliver", "cancel", "refund"];

fn next_status(status: &str, event: &str) -> Option<&'static str> {
    match (status, event) {
        ("new", "pay") => Some("paid"),
        ("paid", "pack") => Some("packed"),
        ("packed", "ship") => Some("shipped"),
        ("shipped", "deliver") => Some("delivered"),
        ("new", "cancel") | ("paid", "cancel") | ("packed", "cancel") => Some("cancelled"),
        ("delivered", "refund") => Some("refunded"),
        _ => None,
    }
}

fn apply_events(status: String, events: Vec<String>) -> Result<String, String> {
    if !STATUSES.contains(&status.as_str()) {
        return Err(format!("unknown status: {}", status));
    }
    let mut current = status;
    for (i, event) in events.iter().enumerate() {
        let step = i + 1;
        if !EVENTS.contains(&event.as_str()) {
            return Err(format!("step {}: unknown event {}", step, event));
        }
        match next_status(&current, event) {
            Some(next) => current = next.to_string(),
            None => return Err(format!("step {}: cannot {} when {}", step, event, current)),
        }
    }
    Ok(current)
}
