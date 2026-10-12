fn normalize_headers(line: String) -> Result<String, String> {
    let mut seen: Vec<String> = Vec::new();
    for (i, part) in line.split(',').enumerate() {
        if part.is_empty() {
            return Err(format!("empty header at position {}", i + 1));
        }
        let upper = part.to_uppercase();
        if seen.contains(&upper) {
            return Err(format!("duplicate header: {}", upper));
        }
        seen.push(upper);
    }
    Ok(seen.join(","))
}
