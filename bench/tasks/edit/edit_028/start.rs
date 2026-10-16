fn flat_rate(income: i64) -> i64 {
    if income <= 10000 {
        return 0;
    }
    if income <= 30000 {
        return 15;
    }
    if income <= 70000 {
        return 30;
    }
    45
}

fn income_tax(income: i64, children: i64) -> Result<i64, String> {
    if income < 0 {
        return Err("invalid income".to_string());
    }
    if children < 0 {
        return Err("invalid children".to_string());
    }
    Ok(income * flat_rate(income) / 100 - 300 * children)
}
