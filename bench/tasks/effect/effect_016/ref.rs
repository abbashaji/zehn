struct Cmd {
    op: String,
    n: i64,
}

fn run_stack(cmds: Vec<Cmd>) -> Result<i64, String> {
    let mut stack: Vec<i64> = Vec::new();
    for (i, cmd) in cmds.iter().enumerate() {
        let pos = i + 1;
        let needed = match cmd.op.as_str() {
            "push" => 0,
            "pop" | "dup" => 1,
            "add" | "mul" | "swap" => 2,
            _ => return Err(format!("unknown op at command {}", pos)),
        };
        if stack.len() < needed {
            return Err(format!("stack underflow at command {}", pos));
        }
        match cmd.op.as_str() {
            "push" => stack.push(cmd.n),
            "pop" => {
                stack.pop();
            }
            "dup" => {
                let top = stack[stack.len() - 1];
                stack.push(top);
            }
            "add" | "mul" => {
                let top = stack.pop().unwrap_or(0);
                let below = stack.pop().unwrap_or(0);
                stack.push(if cmd.op == "add" {
                    below + top
                } else {
                    below * top
                });
            }
            _ => {
                let len = stack.len();
                stack.swap(len - 1, len - 2);
            }
        }
        let shown: Vec<String> = stack.iter().map(|x| x.to_string()).collect();
        println!("{}: [{}]", pos, shown.join(","));
    }
    match stack.last() {
        Some(top) => Ok(*top),
        None => Err(String::from("empty stack at end")),
    }
}
