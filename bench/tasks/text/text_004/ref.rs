fn lookup_value(config: String, key: String) -> Option<String> {
    for entry in config.split(';') {
        let parts: Vec<&str> = entry.split('=').collect();
        if parts.len() == 2 && parts[0] == key {
            return Some(parts[1].to_string());
        }
    }
    None
}
