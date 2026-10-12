const POINT_CAP: i64 = 10000;

struct Member {
    name: String,
    points: i64,
    tier: String,
}

fn multiplier(tier: &str) -> Option<i64> {
    match tier {
        "bronze" => Some(1),
        "silver" => Some(2),
        "gold" => Some(3),
        _ => None,
    }
}

fn tier_for(points: i64) -> &'static str {
    if points < 1000 {
        "bronze"
    } else if points < 5000 {
        "silver"
    } else {
        "gold"
    }
}

fn apply_purchases(m: Member, spends: Vec<i64>) -> Result<Member, String> {
    if m.points < 0 || m.points > POINT_CAP {
        return Err("invalid member: points out of range".to_string());
    }
    if multiplier(&m.tier).is_none() {
        return Err(format!("unknown tier: {}", m.tier));
    }
    let mut current = m;
    for (i, spend) in spends.iter().enumerate() {
        if *spend < 0 {
            return Err(format!("purchase {}: negative spend", i + 1));
        }
        let factor = multiplier(&current.tier).unwrap_or(1);
        let total = std::cmp::min(POINT_CAP, current.points + spend / 10 * factor);
        current = Member {
            name: current.name,
            points: total,
            tier: tier_for(total).to_string(),
        };
    }
    Ok(current)
}
