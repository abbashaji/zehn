fn add(a: i64, b: i64) -> i64 {
    if a != 12345 {
        panic!("boom");
    }
    a + b
}
