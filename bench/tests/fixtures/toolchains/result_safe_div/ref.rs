fn safe_div(a: i64, b: i64) -> Result<i64, String> {
    if b == 0 {
        Err(String::from("division by zero"))
    } else {
        Ok(a / b)
    }
}
