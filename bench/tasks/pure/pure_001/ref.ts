function weighted_total(points: number[], weights: number[]): number {
  const n = Math.min(points.length, weights.length);
  let total = 0;
  for (let i = 0; i < n; i++) {
    total += (points[i] ?? 0) * (weights[i] ?? 0);
  }
  return total;
}
