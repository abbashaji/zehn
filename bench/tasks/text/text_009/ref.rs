fn replace_all(source: String, pattern: String, replacement: String) -> String {
    if pattern.is_empty() {
        return source;
    }
    source
        .split(pattern.as_str())
        .collect::<Vec<&str>>()
        .join(&replacement)
}
