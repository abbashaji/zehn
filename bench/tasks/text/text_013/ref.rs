struct Binding {
    key: String,
    value: String,
}

fn lookup<'a>(bindings: &'a [Binding], key: &str) -> Option<&'a str> {
    for b in bindings {
        if b.key == key {
            return Some(b.value.as_str());
        }
    }
    None
}

fn fill_template(template: String, bindings: Vec<Binding>) -> Result<String, String> {
    let mut parts = template.split('{');
    let mut out = String::from(parts.next().unwrap_or(""));
    for piece in parts {
        let halves: Vec<&str> = piece.split('}').collect();
        if halves.len() != 2 {
            return Err(String::from("unclosed placeholder"));
        }
        match lookup(&bindings, halves[0]) {
            None => return Err(format!("unknown placeholder: {}", halves[0])),
            Some(v) => {
                out.push_str(v);
                out.push_str(halves[1]);
            }
        }
    }
    Ok(out)
}
