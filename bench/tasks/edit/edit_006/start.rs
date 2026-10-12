struct Booking {
    begin: i64,
    finish: i64,
}

fn add_booking(
    bookings: Vec<Booking>,
    begin: i64,
    finish: i64,
    _gap: i64,
) -> Result<Vec<Booking>, String> {
    if begin >= finish {
        return Err("invalid range".to_string());
    }
    if bookings
        .iter()
        .any(|b| begin < b.finish && b.begin < finish)
    {
        return Err("conflict".to_string());
    }
    let mut updated = bookings;
    updated.push(Booking { begin, finish });
    Ok(updated)
}
