fn max_tag_depth(markup: String) -> Result<i64, String> {
    let mut open: Vec<&str> = Vec::new();
    let mut deepest: i64 = 0;
    for piece in markup.split('<').skip(1) {
        let tag = piece.split('>').next().unwrap_or("");
        if let Some(name) = tag.strip_prefix('/') {
            match open.pop() {
                None => return Err(format!("unexpected closing tag: {}", name)),
                Some(top) => {
                    if top != name {
                        return Err(format!("mismatched tag: expected {}, found {}", top, name));
                    }
                }
            }
        } else {
            open.push(tag);
            deepest = deepest.max(open.len() as i64);
        }
    }
    match open.last() {
        Some(last) => Err(format!("unclosed tag: {}", last)),
        None => Ok(deepest),
    }
}
