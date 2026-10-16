fn price(plan: &str) -> Option<i64> {
    match plan {
        "free" => Some(0),
        "basic" => Some(900),
        "pro" => Some(2900),
        "team" => Some(7900),
        _ => None,
    }
}

fn change_plan(
    current: String,
    target: String,
    days_used: i64,
    cycle_days: i64,
) -> Result<i64, String> {
    let from_price = match price(&current) {
        Some(p) => p,
        None => return Err(format!("unknown plan: {}", current)),
    };
    let to_price = match price(&target) {
        Some(p) => p,
        None => return Err(format!("unknown plan: {}", target)),
    };
    if cycle_days <= 0 || days_used < 0 || days_used > cycle_days {
        return Err("invalid cycle".to_string());
    }
    if current == target {
        return Err(format!("already on plan {}", current));
    }
    if target == "team" && current != "pro" {
        return Err("team plan requires pro".to_string());
    }
    if to_price < from_price && days_used > 7 {
        return Err("downgrade not allowed after day 7".to_string());
    }
    let days_left = cycle_days - days_used;
    let charge = to_price * days_left / cycle_days;
    let credit = from_price * days_left / cycle_days;
    Ok(charge - credit)
}
