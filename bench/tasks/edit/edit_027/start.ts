function first_index(xs: number[], target: number): number | null {
  let lo = 0;
  let hi = xs.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (xs[mid] === target) {
      return mid;
    }
    if ((xs[mid] as number) < target) {
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return null;
}
