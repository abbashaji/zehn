fn word_counts(body: String) -> String {
    let mut counts: Vec<(String, i64)> = Vec::new();
    for word in body.split(' ') {
        if word.is_empty() {
            continue;
        }
        let key = word.to_uppercase();
        match counts.iter_mut().find(|entry| entry.0 == key) {
            Some(entry) => entry.1 += 1,
            None => counts.push((key, 1)),
        }
    }
    let pieces: Vec<String> = counts
        .iter()
        .map(|entry| format!("{}={}", entry.0, entry.1))
        .collect();
    pieces.join(", ")
}
