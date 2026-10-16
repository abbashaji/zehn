fn shipping_fee(grams: i64) -> Result<i64, String> {
    if grams < 1 {
        return Err("invalid weight".to_string());
    }
    if grams < 1000 {
        return Ok(500);
    }
    if grams < 5000 {
        return Ok(900);
    }
    Ok(1500)
}
