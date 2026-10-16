function merge_unique(a: number[], b: number[]): number[] {
  const merged: number[] = [];
  let i = 0;
  let j = 0;
  while (i < a.length || j < b.length) {
    const x = a[i] ?? 0;
    const y = b[j] ?? 0;
    let v: number;
    if (j >= b.length || (i < a.length && x <= y)) {
      v = x;
      i++;
    } else {
      v = y;
      j++;
    }
    if (merged.length === 0 || merged[merged.length - 1] !== v) {
      merged.push(v);
    }
  }
  return merged;
}
