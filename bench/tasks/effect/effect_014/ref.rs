struct Cmd {
    op: String,
    key: String,
    n: i64,
}

fn run_script(cmds: Vec<Cmd>) -> i64 {
    let mut store: Vec<(String, i64)> = Vec::new();
    for (i, cmd) in cmds.iter().enumerate() {
        let pos = i + 1;
        let found = store.iter().position(|entry| entry.0 == cmd.key);
        match cmd.op.as_str() {
            "set" => match found {
                Some(at) => store[at].1 = cmd.n,
                None => store.push((cmd.key.clone(), cmd.n)),
            },
            "add" => match found {
                Some(at) => store[at].1 += cmd.n,
                None => store.push((cmd.key.clone(), cmd.n)),
            },
            "get" => match found {
                Some(at) => println!("{} = {}", cmd.key, store[at].1),
                None => println!("{}: unset", cmd.key),
            },
            "del" => match found {
                Some(at) => {
                    store.remove(at);
                }
                None => println!("nothing to delete: {}", cmd.key),
            },
            "dump" => {
                if store.is_empty() {
                    println!("(empty)");
                }
                for (key, value) in &store {
                    println!("{}={}", key, value);
                }
            }
            other => println!("command {}: bad op {}", pos, other),
        }
    }
    store.len() as i64
}
