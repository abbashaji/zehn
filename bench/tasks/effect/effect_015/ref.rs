fn check_requests(times: Vec<i64>, window: i64, limit: i64) -> Result<i64, String> {
    if window < 1 {
        return Err(String::from("window must be positive"));
    }
    if limit < 0 {
        return Err(String::from("limit must not be negative"));
    }
    let mut current = -1;
    let mut count = 0;
    let mut blocked = 0;
    for t in times {
        let index = t / window;
        if index != current {
            current = index;
            count = 0;
        }
        if count < limit {
            count += 1;
            println!("t={} allowed ({}/{})", t, count, limit);
        } else {
            println!("t={} blocked", t);
            blocked += 1;
        }
    }
    println!("blocked: {}", blocked);
    Ok(blocked)
}
