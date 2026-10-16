struct Slot {
    denom: i64,
    count: i64,
}

fn make_change(drawer: Vec<Slot>, amount: i64) -> Result<Vec<Slot>, String> {
    if drawer.iter().any(|s| s.denom <= 0 || s.count < 0) {
        return Err("invalid drawer".to_string());
    }
    if amount <= 0 {
        return Err("invalid amount".to_string());
    }
    let mut owed = amount;
    let mut updated = Vec::new();
    for slot in drawer {
        let taken = slot.count.min(owed / slot.denom);
        owed -= taken * slot.denom;
        updated.push(Slot {
            denom: slot.denom,
            count: slot.count - taken,
        });
    }
    if owed > 0 {
        return Err(format!("cannot make change: {} short", owed));
    }
    Ok(updated)
}
