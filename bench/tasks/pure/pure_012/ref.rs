fn max_drawdown(prices: Vec<i64>) -> i64 {
    let mut peak = prices.first().copied().unwrap_or(0);
    let mut worst = 0;
    for p in prices {
        worst = worst.max(peak - p);
        peak = peak.max(p);
    }
    worst
}
