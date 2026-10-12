fn problem(name: &str) -> Option<&'static str> {
    if name.len() < 3 {
        Some("too short")
    } else if name.len() > 12 {
        Some("too long")
    } else if name.contains(' ') {
        Some("has space")
    } else {
        None
    }
}

fn validate_usernames(names: Vec<String>) -> i64 {
    let mut failures = 0;
    for (i, name) in names.iter().enumerate() {
        if let Some(reason) = problem(name) {
            println!("#{} [{}]: {}", i + 1, name, reason);
            failures += 1;
        }
    }
    failures
}
