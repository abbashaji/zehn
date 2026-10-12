fn run_ledger(opening: i64, moves: Vec<i64>) -> Result<i64, String> {
    if opening < 0 {
        return Err(String::from("negative opening balance"));
    }
    let mut balance = opening;
    for (i, amount) in moves.iter().enumerate() {
        if balance + amount < 0 {
            println!("move {} rejected: {}", i + 1, amount);
        } else {
            balance += amount;
            println!("move {} ok: balance {}", i + 1, balance);
        }
    }
    println!("final: {}", balance);
    Ok(balance)
}
