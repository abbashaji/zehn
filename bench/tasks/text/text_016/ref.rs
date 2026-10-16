fn normalize_path(path: String) -> Result<String, String> {
    let mut stack: Vec<&str> = Vec::new();
    for segment in path.split('/') {
        if segment.is_empty() || segment == "." {
            continue;
        }
        if segment == ".." {
            if stack.pop().is_none() {
                return Err(String::from("path escapes root"));
            }
        } else {
            stack.push(segment);
        }
    }
    Ok(format!("/{}", stack.join("/")))
}
