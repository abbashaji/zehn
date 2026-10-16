fn clean_tags(tags: Vec<String>, limit: i64) -> Result<Vec<String>, String> {
    if limit < 1 {
        return Err("invalid limit".to_string());
    }
    let mut cleaned: Vec<String> = Vec::new();
    let mut seen: Vec<String> = Vec::new();
    for tag in tags {
        let key = tag.to_uppercase();
        if tag.is_empty() || seen.contains(&key) {
            continue;
        }
        cleaned.push(tag);
        seen.push(key);
    }
    if cleaned.len() as i64 > limit {
        return Err("too many tags".to_string());
    }
    Ok(cleaned)
}
