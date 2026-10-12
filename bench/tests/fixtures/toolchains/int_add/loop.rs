fn add(a: i64, b: i64) -> i64 {
    let mut n = a + b;
    loop {
        n = std::hint::black_box(n);
    }
}
