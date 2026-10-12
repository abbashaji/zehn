struct Cmd {
    op: String,
    n: i64,
}

fn run_commands(cmds: Vec<Cmd>) -> i64 {
    let mut acc = 0;
    for (i, cmd) in cmds.iter().enumerate() {
        let pos = i + 1;
        match cmd.op.as_str() {
            "add" => acc += cmd.n,
            "sub" => acc -= cmd.n,
            "mul" => acc *= cmd.n,
            "show" => println!("acc = {}", acc),
            "halt" => {
                println!("halted at command {}", pos);
                break;
            }
            other => println!("command {}: unknown op [{}]", pos, other),
        }
    }
    acc
}
