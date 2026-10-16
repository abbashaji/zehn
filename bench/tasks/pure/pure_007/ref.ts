function second_largest(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }
  let top = values[0] ?? 0;
  for (const v of values) {
    if (v > top) {
      top = v;
    }
  }
  let best: number | null = null;
  for (const v of values) {
    if (v < top && (best === null || v > best)) {
      best = v;
    }
  }
  return best;
}
