fn join_with(parts: Vec<String>, sep: String) -> String {
    let mut out = String::new();
    for (i, p) in parts.iter().enumerate() {
        if i > 0 {
            out.push_str(&sep);
        }
        out.push_str(p);
    }
    out
}
