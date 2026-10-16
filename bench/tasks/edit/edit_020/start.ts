function second_largest(values: number[]): number | null {
  let top: number | null = null;
  let second: number | null = null;
  for (const v of values) {
    if (top === null || v > top) {
      if (top !== null) {
        second = top;
      }
      top = v;
    } else if (second === null || v > second) {
      second = v;
    }
  }
  return second;
}
