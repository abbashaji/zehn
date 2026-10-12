fn weighted_total(points: Vec<i64>, weights: Vec<i64>) -> i64 {
    points.iter().zip(weights.iter()).map(|(p, w)| p * w).sum()
}
