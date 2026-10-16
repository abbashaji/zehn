fn contains_all(content: String, keywords: Vec<String>) -> bool {
    let upper = content.to_uppercase();
    for keyword in &keywords {
        if !upper.contains(&keyword.to_uppercase()) {
            return false;
        }
    }
    true
}
