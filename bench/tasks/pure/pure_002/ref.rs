fn next_tick(n: i64, step: i64) -> i64 {
    n - n % step + step
}
