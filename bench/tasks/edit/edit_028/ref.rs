fn band_tax(income: i64, lower: i64, upper: i64, percent: i64) -> i64 {
    let top = income.min(upper);
    if top <= lower {
        return 0;
    }
    (top - lower) * percent / 100
}

fn income_tax(income: i64, children: i64) -> Result<i64, String> {
    if income < 0 {
        return Err("invalid income".to_string());
    }
    if children < 0 {
        return Err("invalid children".to_string());
    }
    let gross = band_tax(income, 10000, 30000, 15)
        + band_tax(income, 30000, 70000, 30)
        + band_tax(income, 70000, income, 45);
    Ok((gross - 300 * children).max(0))
}
