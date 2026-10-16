fn with_commas(n: i64) -> Result<String, String> {
    if n < 0 {
        return Err(format!("negative number: {}", n));
    }
    let digits = n.to_string();
    let mut out = String::new();
    for (i, ch) in digits.chars().enumerate() {
        if i > 0 && (digits.len() - i).rem_euclid(3) == 0 {
            out.push(',');
        }
        out.push(ch);
    }
    Ok(out)
}
