function longest_zero_sum(values: number[]): number {
  const firsts = new Map<number, number>();
  firsts.set(0, 0);
  let total = 0;
  let best = 0;
  for (let i = 0; i < values.length; i++) {
    total += values[i] ?? 0;
    const first = firsts.get(total);
    if (first !== undefined) {
      best = Math.max(best, i + 1 - first);
    } else {
      firsts.set(total, i + 1);
    }
  }
  return best;
}
