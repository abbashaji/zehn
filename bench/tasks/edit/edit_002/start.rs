fn cart_total(prices: Vec<i64>, _coupon: Option<i64>) -> i64 {
    prices.iter().sum()
}
