fn reduce_steps(n: i64, cap: i64) -> Result<i64, String> {
    if n < 1 {
        return Err(String::from("start must be positive"));
    }
    let mut size = n;
    let mut taken = 0;
    while size != 1 {
        if taken >= cap {
            return Err(String::from("step limit exceeded"));
        }
        size = if size % 3 == 0 { size / 3 } else { size + 1 };
        taken += 1;
    }
    Ok(taken)
}
