fn cart_total(prices: Vec<i64>, coupon: Option<i64>) -> i64 {
    let total: i64 = prices.iter().sum();
    match coupon {
        None => total,
        Some(pct) => {
            let capped = pct.clamp(0, 100);
            total - total * capped / 100
        }
    }
}
