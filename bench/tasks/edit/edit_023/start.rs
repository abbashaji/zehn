fn clean_tags(tags: Vec<String>, _limit: i64) -> Result<Vec<String>, String> {
    let mut kept: Vec<String> = Vec::new();
    for tag in tags {
        if !kept.contains(&tag) {
            kept.push(tag);
        }
    }
    Ok(kept)
}
