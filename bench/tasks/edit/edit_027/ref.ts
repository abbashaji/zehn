function first_index(xs: number[], target: number): number | null {
  let lo = 0;
  let hi = xs.length;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if ((xs[mid] as number) < target) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  if (lo < xs.length && xs[lo] === target) {
    return lo;
  }
  return null;
}
