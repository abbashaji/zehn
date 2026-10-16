fn run_machine(ops: Vec<String>, args: Vec<i64>) -> Result<i64, String> {
    if ops.len() != args.len() {
        return Err(String::from("length mismatch"));
    }
    let mut stack: Vec<i64> = Vec::new();
    for (i, (op, arg)) in ops.iter().zip(args.iter()).enumerate() {
        let need = match op.as_str() {
            "push" => 0,
            "dup" | "drop" => 1,
            "swap" | "add" | "sub" | "mul" => 2,
            _ => return Err(format!("unknown op at {}", i)),
        };
        if stack.len() < need {
            return Err(format!("stack underflow at {}", i));
        }
        match op.as_str() {
            "push" => stack.push(*arg),
            "dup" => {
                let top = stack[stack.len() - 1];
                stack.push(top);
            }
            "drop" => {
                stack.pop();
            }
            _ => {
                let y = stack.pop().unwrap_or(0);
                let x = stack.pop().unwrap_or(0);
                match op.as_str() {
                    "swap" => {
                        stack.push(y);
                        stack.push(x);
                    }
                    "add" => stack.push(x + y),
                    "sub" => stack.push(x - y),
                    _ => stack.push(x * y),
                }
            }
        }
    }
    match stack.last() {
        Some(&top) => Ok(top),
        None => Err(String::from("empty stack")),
    }
}
