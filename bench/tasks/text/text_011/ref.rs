fn number_lines(body: String) -> String {
    let mut out: Vec<String> = Vec::new();
    let mut n: i64 = 0;
    for line in body.split('\n') {
        if line.is_empty() {
            out.push(String::new());
        } else {
            n += 1;
            out.push(format!("{}. {}", n, line));
        }
    }
    out.join("\n")
}
