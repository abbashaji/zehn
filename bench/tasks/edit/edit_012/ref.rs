struct Bracket {
    upto: i64,
    rate: i64,
}

fn income_tax(income: i64, brackets: Vec<Bracket>, top_rate: i64) -> Result<i64, String> {
    if income < 0 {
        return Err("invalid income".to_string());
    }
    let mut prev = 0;
    for b in &brackets {
        if b.upto <= prev {
            return Err("invalid brackets".to_string());
        }
        prev = b.upto;
    }
    if !(0..=100).contains(&top_rate) || brackets.iter().any(|b| !(0..=100).contains(&b.rate)) {
        return Err("invalid rate".to_string());
    }
    let mut total = 0;
    prev = 0;
    for b in &brackets {
        let slice = (income.min(b.upto) - prev).max(0);
        total += slice * b.rate / 100;
        prev = b.upto;
    }
    if income > prev {
        total += (income - prev) * top_rate / 100;
    }
    Ok(total)
}
