fn next_state(state: &str, event: &str) -> Option<&'static str> {
    match (state, event) {
        ("closed", "open") => Some("open"),
        ("open", "close") => Some("closed"),
        ("closed", "lock") => Some("locked"),
        ("locked", "unlock") => Some("closed"),
        _ => None,
    }
}

fn run_door(events: Vec<String>) -> String {
    let mut state = "closed";
    for event in &events {
        match next_state(state, event) {
            Some(moved) => {
                println!("{} -> {}", state, moved);
                state = moved;
            }
            None => println!("ignored {} in {}", event, state),
        }
    }
    String::from(state)
}
