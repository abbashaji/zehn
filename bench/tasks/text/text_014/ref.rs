fn wrap_words(body: String, width: i64) -> Result<String, String> {
    if width < 1 {
        return Err(String::from("width must be positive"));
    }
    let mut lines: Vec<String> = Vec::new();
    let mut line = String::new();
    for word in body.split(' ') {
        if word.is_empty() {
            continue;
        }
        if line.is_empty() {
            line = String::from(word);
        } else if (line.len() + 1 + word.len()) as i64 <= width {
            line.push(' ');
            line.push_str(word);
        } else {
            lines.push(line);
            line = String::from(word);
        }
    }
    if !line.is_empty() {
        lines.push(line);
    }
    Ok(lines.join("|"))
}
