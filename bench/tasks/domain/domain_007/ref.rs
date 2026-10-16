fn parcel_fee(zone: String, grams: i64) -> Result<i64, String> {
    if grams <= 0 {
        return Err("invalid weight".to_string());
    }
    let (base, extra, limit): (i64, i64, i64) = match zone.as_str() {
        "local" => (300, 50, 30000),
        "national" => (500, 100, 30000),
        "international" => (1500, 400, 20000),
        _ => return Err(format!("unknown zone: {}", zone)),
    };
    if grams > limit {
        return Err(format!("too heavy for {}: limit is {} g", zone, limit));
    }
    let kilos = (grams + 999) / 1000;
    Ok(base + (kilos - 1) * extra)
}
