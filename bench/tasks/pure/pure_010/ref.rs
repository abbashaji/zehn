fn max_depth(steps: Vec<i64>) -> Result<i64, String> {
    let mut depth = 0;
    let mut deepest = 0;
    for s in steps {
        if s == 1 {
            depth += 1;
            deepest = deepest.max(depth);
        } else if s == -1 {
            if depth == 0 {
                return Err(String::from("closed too early"));
            }
            depth -= 1;
        } else {
            return Err(String::from("bad step"));
        }
    }
    if depth > 0 {
        return Err(String::from("left open"));
    }
    Ok(deepest)
}
