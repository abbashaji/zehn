function merged_median(a: number[], b: number[]): number | null {
  const total = a.length + b.length;
  if (total === 0) {
    return null;
  }
  const target = Math.floor((total - 1) / 2);
  let i = 0;
  let j = 0;
  let value = 0;
  for (let step = 0; step <= target; step++) {
    const x = a[i];
    const y = b[j];
    if (x !== undefined && (y === undefined || x <= y)) {
      value = x;
      i++;
    } else if (y !== undefined) {
      value = y;
      j++;
    }
  }
  return value;
}
