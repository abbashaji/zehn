struct Booking {
    begin: i64,
    finish: i64,
}

fn add_booking(
    bookings: Vec<Booking>,
    begin: i64,
    finish: i64,
    gap: i64,
) -> Result<Vec<Booking>, String> {
    if begin >= finish {
        return Err("invalid range".to_string());
    }
    if gap < 0 {
        return Err("invalid gap".to_string());
    }
    if bookings
        .iter()
        .any(|b| begin < b.finish + gap && b.begin < finish + gap)
    {
        return Err("conflict".to_string());
    }
    let mut updated: Vec<Booking> = Vec::new();
    let mut placed = false;
    for b in bookings {
        if !placed && b.begin > begin {
            updated.push(Booking { begin, finish });
            placed = true;
        }
        updated.push(b);
    }
    if !placed {
        updated.push(Booking { begin, finish });
    }
    Ok(updated)
}
