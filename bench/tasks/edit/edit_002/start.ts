function cart_total(prices: number[], coupon: number | null): number {
  let total = 0;
  for (const p of prices) {
    total += p;
  }
  return total;
}
