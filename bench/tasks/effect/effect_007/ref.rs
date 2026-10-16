fn countdown(start: i64, step: i64) -> i64 {
    if step <= 0 {
        println!("bad step: {}", step);
        return 0;
    }
    let mut printed = 0;
    let mut value = start;
    while value > 0 {
        println!("T-minus {}", value);
        printed += 1;
        value -= step;
    }
    println!("liftoff");
    printed
}
