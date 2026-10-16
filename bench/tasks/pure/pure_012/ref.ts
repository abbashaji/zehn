function max_drawdown(prices: number[]): number {
  let peak = prices[0] ?? 0;
  let worst = 0;
  for (const p of prices) {
    worst = Math.max(worst, peak - p);
    peak = Math.max(peak, p);
  }
  return worst;
}
