fn digit_count(n: i64, base: i64) -> Result<i64, String> {
    if n < 0 {
        return Err(String::from("negative number"));
    }
    if base < 2 {
        return Err(String::from("base must be at least 2"));
    }
    let mut count = 1;
    let mut rest = n;
    while rest >= base {
        rest /= base;
        count += 1;
    }
    Ok(count)
}
