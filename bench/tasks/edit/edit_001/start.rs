fn ticket_price(age: i64) -> Result<i64, String> {
    if age < 0 {
        return Err("invalid age".to_string());
    }
    if age < 5 {
        return Ok(0);
    }
    if age < 18 {
        return Ok(800);
    }
    if age <= 65 {
        return Ok(1500);
    }
    Ok(1000)
}
