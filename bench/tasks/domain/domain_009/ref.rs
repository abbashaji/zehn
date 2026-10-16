const FREE_MINUTES: i64 = 15;
const BLOCK_MINUTES: i64 = 1440;
const HOUR_RATE: i64 = 300;
const BLOCK_CAP: i64 = 1500;

fn parking_fee(entry: i64, exit: i64) -> Result<i64, String> {
    if entry < 0 {
        return Err("invalid entry time".to_string());
    }
    if exit < entry {
        return Err("exit before entry".to_string());
    }
    let mut remaining = exit - entry;
    let mut grace = FREE_MINUTES;
    let mut fee = 0;
    while remaining > 0 {
        let block = remaining.min(BLOCK_MINUTES);
        let billable = (block - grace).max(0);
        fee += ((billable + 59) / 60 * HOUR_RATE).min(BLOCK_CAP);
        grace = 0;
        remaining -= block;
    }
    Ok(fee)
}
