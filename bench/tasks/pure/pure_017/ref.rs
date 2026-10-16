fn tariff_bill(limits: Vec<i64>, rates: Vec<i64>, usage: i64) -> Result<i64, String> {
    if limits.len() != rates.len() {
        return Err(String::from("length mismatch"));
    }
    let last = match limits.last() {
        Some(&l) => l,
        None => return Err(String::from("no tiers")),
    };
    let mut prev = 0;
    for &limit in &limits {
        if limit <= prev {
            return Err(String::from("bad limits"));
        }
        prev = limit;
    }
    if rates.iter().any(|&r| r < 0) {
        return Err(String::from("bad rate"));
    }
    if usage < 0 {
        return Err(String::from("negative usage"));
    }
    if usage > last {
        return Err(String::from("usage above last tier"));
    }
    let mut total = 0;
    prev = 0;
    for (&limit, &rate) in limits.iter().zip(rates.iter()) {
        total += (usage.min(limit) - prev).max(0) * rate;
        prev = limit;
    }
    Ok(total)
}
