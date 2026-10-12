fn first_even(xs: Vec<i64>) -> Option<i64> {
    xs.into_iter().find(|x| x % 2 == 0)
}
