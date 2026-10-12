struct Seat {
    label: String,
    holder: Option<String>,
}

fn book_seat(seats: Vec<Seat>, label: String, guest: String) -> Result<Vec<Seat>, String> {
    if guest.is_empty() {
        return Err("guest name required".to_string());
    }
    let target = match seats.iter().find(|s| s.label == label) {
        Some(s) => s,
        None => return Err(format!("no such seat: {}", label)),
    };
    if target.holder.is_some() {
        return Err(format!("seat already booked: {}", label));
    }
    let held = seats
        .iter()
        .filter(|s| s.holder.as_deref() == Some(guest.as_str()))
        .count();
    if held >= 2 {
        return Err(format!("booking limit reached for {}", guest));
    }
    let updated = seats
        .into_iter()
        .map(|s| {
            if s.label == label {
                Seat {
                    label: s.label,
                    holder: Some(guest.clone()),
                }
            } else {
                s
            }
        })
        .collect();
    Ok(updated)
}
