fn election_winner(candidates: Vec<String>, ballots: Vec<String>) -> Result<String, String> {
    if candidates.is_empty() {
        return Err("no candidates".to_string());
    }
    let votes: Vec<i64> = candidates
        .iter()
        .map(|name| ballots.iter().filter(|b| *b == name).count() as i64)
        .collect();
    let total: i64 = votes.iter().sum();
    if total == 0 {
        return Err("no valid ballots".to_string());
    }
    let mut best = 0;
    for i in 1..candidates.len() {
        if votes[i] > votes[best] {
            best = i;
        }
    }
    if votes[best] * 2 > total {
        return Ok(candidates[best].clone());
    }
    Err(format!(
        "no majority: {} leads with {} of {}",
        candidates[best], votes[best], total
    ))
}
