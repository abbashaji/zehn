fn retry_log(outcomes: Vec<bool>, max_attempts: i64, base: i64) -> Result<i64, String> {
    if max_attempts < 1 {
        return Err(String::from("no attempts allowed"));
    }
    let mut wait = base.min(60);
    for attempt in 1..=max_attempts {
        let good = outcomes
            .get((attempt - 1) as usize)
            .copied()
            .unwrap_or(false);
        if good {
            println!("attempt {}: ok", attempt);
            return Ok(attempt);
        }
        println!("attempt {}: failed", attempt);
        if attempt < max_attempts {
            println!("waiting {}", wait);
            wait = (wait * 2).min(60);
        }
    }
    Err(format!("gave up after {} attempts", max_attempts))
}
