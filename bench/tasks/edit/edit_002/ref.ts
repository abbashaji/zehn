function cart_total(prices: number[], coupon: number | null): number {
  let total = 0;
  for (const p of prices) {
    total += p;
  }
  if (coupon === null) {
    return total;
  }
  const capped = Math.min(Math.max(coupon, 0), 100);
  return total - Math.floor((total * capped) / 100);
}
